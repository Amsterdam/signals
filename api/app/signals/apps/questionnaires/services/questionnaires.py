# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import logging

from django.core.exceptions import ValidationError as django_validation_error
from django.utils import timezone

from signals.apps.questionnaires.exceptions import SessionExpired, SessionFrozen, SessionInvalidated
from signals.apps.questionnaires.fieldtypes import get_field_type_class
from signals.apps.questionnaires.models import Answer, Questionnaire, Session
from signals.apps.questionnaires.services.feedback_request import FeedbackRequestService
from signals.apps.questionnaires.services.reaction_request import ReactionRequestService
from signals.apps.signals import workflow

logger = logging.getLogger(__name__)


class QuestionnairesService:
    @staticmethod
    def create_session(questionnaire, submit_before=None, duration=None):
        if duration:
            return Session.objects.create(
                questionnaire=questionnaire,
                submit_before=submit_before,
                duration=duration
            )
        return Session.objects.create(questionnaire=questionnaire, submit_before=submit_before)

    @staticmethod
    def get_session(uuid):
        """
        Get sessions, that are not frozen, expired or in wrong state for given flow.
        """
        session = Session.objects.get(uuid=uuid)

        # Reaction was already provided (hence form filled out, and hence session.frozen):
        if session.frozen:
            raise SessionFrozen('Already used!')

        # Reaction was not provided in time and therefore this session expired:
        if session.is_expired:
            raise SessionExpired('Expired!')

        if session.questionnaire.flow == Questionnaire.REACTION_REQUEST:
            signal = session._signal

            # Check that a signal is associated with this session
            if signal is None:
                msg = f'Session {session.uuid} is not associated with a Signal.'
                logger.warning(msg, stack_info=True)
                raise SessionInvalidated(msg)

            # Make sure that the signal is in state REACTIE_GEVRAAGD.
            if signal.status.state != workflow.REACTIE_GEVRAAGD:
                msg = f'Session {session.uuid} is invalidated, associated signal not in state REACTIE_GEVRAAGD.'
                logger.warning(msg, stack_info=True)
                raise SessionInvalidated(msg)

            # Make sure that only the most recent Session and associated
            # Questionnaire and Question can be answered:
            most_recent_session = Session.objects.filter(
                _signal=signal, questionnaire__flow=Questionnaire.REACTION_REQUEST).order_by('created_at').last()
            if most_recent_session.uuid != session.uuid:
                msg = f'Session {session.uuid} is invalidated, a newer reaction request was issued.'
                raise SessionInvalidated(msg)

        return session

    @staticmethod
    def validate_answer_payload(answer_payload, question):  # noqa: C901
        # If a question is not required the answer payload must be JSON null,
        # anything else gets the schema check.
        if not question.required and answer_payload is None:
            return answer_payload

        # FieldType subclass schema check
        field_type_class = get_field_type_class(question)
        field_type_class().validate_submission_payload(answer_payload)

        # If a questions has pre-defined answers (see the Choice model), the
        # answer payload should match one of these predefined answers.
        if not question.enforce_choices:
            return answer_payload

        if valid_payloads := question.choices.values_list('payload', flat=True):
            for valid_payload in valid_payloads:
                if answer_payload == valid_payload:
                    return answer_payload
            else:
                msg = 'Submitted answer does not match one of the pre-defined answers.'
                raise django_validation_error(msg)

    @staticmethod
    def create_answer(answer_payload, question, questionnaire, session=None):
        # TODO: check that question is actually part of the questionnaire!!!
        # TODO: consider case where second question of questionnaire is answered
        # first when there is no session should we disallow this??

        # First check that we have a session create it if not. Furthermore check
        # that our session is neither expired nor frozen.
        if session is None:
            session = QuestionnairesService.create_session(questionnaire)

        if not session.started_at:
            session.started_at = timezone.now()
            session.save()

        if session.is_expired:
            raise SessionExpired(f'Session {session.uuid} expired.')

        if session.frozen:
            raise SessionFrozen(f'Session {session.uuid} frozen.')

        # Check submitted answer validates. If so save it to DB and return it.
        QuestionnairesService.validate_answer_payload(answer_payload, question)

        return Answer.objects.create(session=session, question=question, payload=answer_payload)

    @staticmethod
    def freeze_session(session):
        session.frozen = True
        session.save()

        QuestionnairesService.handle_frozen_session(session)
        return session

    @staticmethod
    def handle_frozen_session(session):
        if session.questionnaire.flow == Questionnaire.REACTION_REQUEST:
            ReactionRequestService.handle_frozen_session_REACTION_REQUEST(session)
        elif session.questionnaire.flow == Questionnaire.FEEDBACK_REQUEST:
            FeedbackRequestService.handle_frozen_session_FEEDBACK_REQUEST(session)

    @staticmethod
    def get_next_question(answer_payload, question, graph):
        """
        Get next question given an Answer payload and Question and QuestionGraph.
        """
        outgoing_edges = graph.edges.filter(question=question).select_related('choice')

        for edge in outgoing_edges:
            if edge.choice and edge.choice.payload == answer_payload or edge.choice is None:
                return edge.next_question

        return None

    @staticmethod
    def get_latest_answers(session):
        """
        Queryset of Answers with only the latest answer per Question.
        """
        # Postgres only: https://docs.djangoproject.com/en/3.2/ref/models/querysets/#distinct
        # We want the most recent answer per unique question in effect letting
        # clients overwrite answers to fix mistakes. However, if several questions
        # have the same analysis_key property, this queryset will still return
        # several answers for that analysis_key. The latter problem is addressed
        # by get_latest_answers_by_analysis_key method below.
        latest_answers = (
            Answer.objects.filter(session=session)
            .order_by('question_id', '-created_at')
            .distinct('question_id')
            .select_related('question')
        )

        return latest_answers

    def get_latest_answers_by_analysis_key(session):
        """
        Get Answers in a dictionary keyed by their Question's analysis_key.

        Note: As the Question model does not require an analysis_key, not all
        answers for this session may be returned.
        """
        answers = QuestionnairesService.get_latest_answers(session)
        by_analysis_key = {}
        for answer in answers.all():
            key = answer.question.analysis_key

            # If several questions in a questionnaire have the same analysis_key
            # we will use the answer with the latest created_at timestamp.
            if key in by_analysis_key:
                if answer.created_at > by_analysis_key[key].created_at:
                    by_analysis_key[key] = answer
            else:
                by_analysis_key[key] = answer

        return by_analysis_key

    def get_latest_answers_by_uuid(session):
        """
        Get Answers in a dictionary keyed by their Question's UUID.
        """
        answers = QuestionnairesService.get_latest_answers(session)
        return {a.question.uuid: a for a in answers}

    def validate_session_using_question_graph(session):
        """
        Given a session validate whether all required answers along a path in a
        question graph were received.
        """
        # TODO: consider allowing no more answers than questions
        by_uuid = QuestionnairesService.get_latest_answers_by_uuid(session)
        graph = session.questionnaire.graph

        if not graph.first_question:
            raise django_validation_error('Question graph contains no questions.')

        errors = {}

        q = graph.first_question
        while q:
            # Check that we have all required answers:
            answer = by_uuid.get(q.uuid, None)
            if not answer and q.required:
                errors[str(q.uuid)] = 'Question not answered'

            if answer:
                q = QuestionnairesService.get_next_question(answer.payload, q, graph)
            else:
                q = QuestionnairesService.get_next_question(None, q, graph)

        if errors:
            raise django_validation_error(errors)

        return session

    @staticmethod
    def get_extra_properties_from_answer(session):
        pass

    @staticmethod
    def get_extra_properties_from_session(session):
        pass
