# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import logging

import jsonschema
from django.core.exceptions import ValidationError as django_validation_error
from django.db import transaction
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
    def create_session(questionnaire, submit_before=None, ttl_seconds=None):
        if ttl_seconds:
            return Session.objects.create(
                questionnaire=questionnaire,
                submit_before=submit_before,
                ttl_seconds=ttl_seconds
            )
        return Session.objects.create(questionnaire=questionnaire, submit_before=submit_before)

    @staticmethod
    def get_session(uuid):
        session = Session.objects.get(uuid=uuid)
        if session.questionnaire.flow == Questionnaire.REACTION_REQUEST:
            signal = session._signal

            # Check that a signal is associated with this session
            if signal is None:
                msg = f'Session {session.uuid} is not associated with a Signal.'
                logger.warning(msg, stack_info=True)
                raise SessionInvalidated(msg)

            # Make sure that the signal is in state REACTIE_GEVRAAGD.
            if signal.status.state != workflow.REACTIE_GEVRAAGD:
                msg = f'Session {session.uuid} is invalidated.'
                logger.warning(msg, stack_info=True)
                raise SessionInvalidated(msg)

            # Make sure that only the most recent Session and associated
            # Questionnaire and Question can be answered:
            most_recent_session = Session.objects.filter(
                _signal=signal, questionnaire__flow=Questionnaire.REACTION_REQUEST).order_by('created_at').last()
            if most_recent_session.uuid != session.uuid:
                raise SessionInvalidated(f'Session {session.uuid} is invalidated.')

        return session

    @staticmethod
    def validate_answer_payload(answer_payload, question):
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

        return answer_payload

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

        # Check submitted answer
        answer_payload = QuestionnairesService.validate_answer_payload(answer_payload, question)

        # Check whether the (equivalent of) a submit button was used, if so
        # freeze the session.
        with transaction.atomic():
            if question.key == 'submit':
                transaction.on_commit(lambda: QuestionnairesService.handle_frozen_session(session))
                session.frozen = True
                session.save()
            answer = Answer.objects.create(session=session, question=question, payload=answer_payload)

        return answer

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
            if question.key == 'submit':
                next_question = None
            else:
                next_question = Question.objects.get_by_reference(ref='submit')
        else:
            try:
                next_question = Question.objects.get_by_reference(ref=next_ref)
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
