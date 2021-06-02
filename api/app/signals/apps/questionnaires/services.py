# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import jsonschema
from django.core.exceptions import ValidationError as django_validation_error
from django.utils import timezone
from jsonschema.exceptions import SchemaError as js_schema_error
from jsonschema.exceptions import ValidationError as js_validation_error

from signals.apps.questionnaires.exceptions import SessionExpired, SessionFrozen
from signals.apps.questionnaires.fieldtypes import get_field_type_class
from signals.apps.questionnaires.models import Answer, Session


class QuestionnairesService:
    @staticmethod
    def is_expired(session):
        if session.submit_before and session.submit_before <= timezone.now():
            return True
        elif session.started_at + session.duration <= timezone.now():
            return True
        return False

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
    def validate_answer_payload(answer_payload, question):
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
        # First check that we have a session create it if not. Furthermore check
        # that our session is neither expired nor frozen.
        if session is None:
            session = QuestionnairesService.create_session(questionnaire)

        if not session.started_at:
            session.started_at = timezone.now()
            session.save()

        if QuestionnairesService.is_expired(session):
            raise SessionExpired(f'Session {session.uuid} expired.')

        if session.frozen:
            raise SessionFrozen(f'Session {session.uuid} frozen.')

        # Check submitted answer
        answer_payload = QuestionnairesService.validate_answer_payload(answer_payload, question)

        return Answer.objects.create(session=session, question=question, payload=answer_payload)

    @staticmethod
    def get_next_question_key(answer, question):
        answer_payload = answer.payload
        if 'next' in question.payload and question.payload['next']:
            for rule in question.payload['next']:
                if answer_payload == rule['payload']:
                    return rule['key']
        return None

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
