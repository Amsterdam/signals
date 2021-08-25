# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import logging

import jsonschema
from django.core.exceptions import ValidationError as django_validation_error
from django.utils import timezone
from jsonschema.exceptions import SchemaError as js_schema_error
from jsonschema.exceptions import ValidationError as js_validation_error

from signals.apps.questionnaires.exceptions import SessionExpired, SessionFrozen, SessionInvalidated
from signals.apps.questionnaires.fieldtypes import get_field_type_class
from signals.apps.questionnaires.models import Answer, Question, Questionnaire, Session
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

        # Schema check
        field_type_class = get_field_type_class(question)

        try:
            jsonschema.validate(answer_payload, field_type_class.submission_schema)
        except js_schema_error:
            msg = f'JSONSchema for {field_type_class.__name__} is not valid.'
            raise django_validation_error(msg)
        except js_validation_error:
            msg = 'Submitted answer does not validate.'
            raise django_validation_error(msg)

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

    @staticmethod
    def get_next_question_ref(answer_payload, question, graph):
        # TODO: consider whether we want case sensitive matches in case of
        # character strings
        outgoing_edges = graph.edges.filter(question=question)
        for edge in outgoing_edges:
            if edge.payload == answer_payload or edge.payload is None:
                return edge.next_question.ref

        return None

    @staticmethod
    def get_next_question(answer, question):
        graph = answer.session.questionnaire.graph
        next_ref = QuestionnairesService.get_next_question_ref(answer.payload, question, graph)

        if next_ref is None:
            next_question = None
        else:
            try:
                next_question = Question.objects.get_by_reference(next_ref)
            except Question.DoesNotExist:
                return None  # TODO: consider raising an exception

        return next_question

    @staticmethod
    def get_answers(session):
        # - only newest answer per question
        pass

    @staticmethod
    def get_extra_properties_from_answer(session):
        pass

    @staticmethod
    def get_extra_properties_from_session(session):
        pass
