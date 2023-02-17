# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import uuid

from django.core.exceptions import ValidationError
from django.test import TestCase

from signals.apps.questionnaires.factories import SessionFactory
from signals.apps.questionnaires.models import Questionnaire, Session
from signals.apps.questionnaires.services import (
    FeedbackRequestSessionService,
    ReactionRequestSessionService,
    SessionService
)
from signals.apps.questionnaires.services.utils import get_session_service


class TestGetSessionService(TestCase):
    def setUp(self):
        self.session_extra_properties = SessionFactory.create(questionnaire__flow=Questionnaire.EXTRA_PROPERTIES)
        self.session_reaction_request = SessionFactory.create(questionnaire__flow=Questionnaire.REACTION_REQUEST)
        self.session_feedback_request = SessionFactory.create(questionnaire__flow=Questionnaire.FEEDBACK_REQUEST)

    def test_get_session_service_by_uuid(self):
        service_extra_properties = get_session_service(self.session_extra_properties.uuid)
        self.assertIsInstance(service_extra_properties, SessionService)

        service_reaction_request = get_session_service(self.session_reaction_request.uuid)
        self.assertIsInstance(service_reaction_request, ReactionRequestSessionService)

        service_feedback_request = get_session_service(self.session_feedback_request.uuid)
        self.assertIsInstance(service_feedback_request, FeedbackRequestSessionService)

    def test_get_session_service_by_session(self):
        service_extra_properties = get_session_service(self.session_extra_properties)
        self.assertIsInstance(service_extra_properties, SessionService)

        service_reaction_request = get_session_service(self.session_reaction_request)
        self.assertIsInstance(service_reaction_request, ReactionRequestSessionService)

        service_feedback_request = get_session_service(self.session_feedback_request)
        self.assertIsInstance(service_feedback_request, FeedbackRequestSessionService)

    def test_get_session_service_no_session(self):
        session_uuid = uuid.uuid4()

        while Session.objects.filter(uuid=session_uuid).count() > 0:
            session_uuid = uuid.uuid4()

        with self.assertRaises(Session.DoesNotExist):
            get_session_service(session_uuid)

        with self.assertRaises(Session.DoesNotExist):
            uuid_str = str(session_uuid)
            get_session_service(uuid_str)

    def test_get_session_service_no_uuid(self):
        with self.assertRaises(ValidationError):
            get_session_service('THIS IS NOT A UUID')
