# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Test the reaction request flow at the REST API level.
"""
import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import override_settings
from django.urls import include, path
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.api.views import NamespaceView
from signals.apps.questionnaires.app_settings import REACTION_REQUEST_DAYS_OPEN
from signals.apps.questionnaires.factories import AnswerFactory
from signals.apps.questionnaires.models import Session
from signals.apps.questionnaires.services.reaction_request import (
    create_session_for_reaction_request
)
from signals.apps.questionnaires.tests.mixin import ValidateJsonSchemaMixin
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory

THIS_DIR = os.path.dirname(__file__)

urlpatterns = [
    path('v1/relations/', NamespaceView.as_view(), name='signal-namespace'),
    path('', include('signals.apps.questionnaires.urls')),
]


class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns


@override_settings(ROOT_URLCONF=test_urlconf)
class TestRetrieveReactionRequest(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/public/qa/questions/'
    session_detail_endpoint = '/public/qa/sessions/{uuid}/'
    question_detail_endpoint = '/public/qa/questions/{ref}'

    def setUp(self):
        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_get_question_detail.json')
        )
        self.post_answer_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_post_question_answer_response.json')
        )
        self.session_detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_get_session_detail.json')
        )

        self.t_creation = datetime(2021, 10, 1, 0, 0, 0)
        seconds_open = REACTION_REQUEST_DAYS_OPEN * 24 * 60 * 60
        self.t_answer_in_time = self.t_creation + timedelta(seconds=seconds_open / 2)
        self.t_answer_too_late = self.t_creation + timedelta(seconds=seconds_open * 2)

        with freeze_time(self.t_creation):
            self.signal = SignalFactory.create(
                created_at=self.t_creation,
                status__state=workflow.REACTIE_GEVRAAGD,
                status__text='SOME QUESTION'
            )
            self.session = create_session_for_reaction_request(self.signal)

        self.assertIsInstance(self.session, Session)
        self.assertEqual(self.session._signal.status.state, workflow.REACTIE_GEVRAAGD)

        self.session_url = self.session_detail_endpoint.format(uuid=str(self.session.uuid))

    @patch('signals.apps.questionnaires.rest_framework.fields.SessionPublicHyperlinkedIdentityField.get_url',
           autospec=True)
    def test_retrieve_session(self, patched_get_url):
        """
        Happy flow retrieving a non-invalidated session in time.
        """
        patched_get_url.return_value = '/some/url/'

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)
        response_json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertJsonSchema(self.session_detail_schema, response_json)

    def test_retrieve_session_too_late(self):
        """
        Retrieve session after it expired.
        """
        with freeze_time(self.t_answer_too_late):
            response = self.client.get(self.session_url)

        response_json = response.json()

        self.assertEqual(response.status_code, 410)
        self.assertEqual(response_json['detail'], 'Expired!')

    def test_retrieve_session_filled_out_already(self):
        """
        Retrieve session that was filled out and frozen already.
        """
        question = self.session.questionnaire.first_question
        AnswerFactory.create(
            session=self.session, question=question, payload='SOME ANSWER')
        self.session.frozen = True
        self.session.save()
        self.session.refresh_from_db()

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)
        response_json = response.json()

        self.assertEqual(response.status_code, 410)
        self.assertEqual(response_json['detail'], 'Already used!')

    def test_retrieve_session_reaction_request_superseded(self):
        """
        Retrieve session for which a newer reaction request was created.
        """
        with freeze_time(self.t_answer_in_time):
            new_status = StatusFactory.create(_signal=self.signal, state=workflow.REACTIE_GEVRAAGD, text='NEW QUESTION')
            self.signal.status = new_status
            self.signal.save()
        self.signal.refresh_from_db()

        # create new session, but retrieve the old one
        create_session_for_reaction_request(self.signal)
        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)
        response_json = response.json()

        self.assertEqual(response.status_code, 500)
        expected = f'Session {self.session.uuid} is invalidated, a newer reaction request was issued.'
        self.assertEqual(response_json['detail'], expected)

    def test_retrieve_session_signal_state_not_REACTIE_GEVRAAGD(self):
        """
        Retrieve session for which signal is no longer in state REACTIE_GEVRAAGD
        """
        new_status = StatusFactory.create(state=workflow.GEMELD, text='NEW STATE', _signal=self.signal)
        new_status.save()
        self.signal.status = new_status
        self.signal.save()
        self.signal.refresh_from_db()

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)
        response_json = response.json()

        self.assertEqual(response.status_code, 500)
        expected = f'Session {self.session.uuid} is invalidated, associated signal not in state REACTIE_GEVRAAGD.'
        self.assertEqual(response_json['detail'], expected)

    def test_retrieve_session_does_not_exist(self):
        """
        Retrieve session which does not exist yields 404
        """
        session_uuid = uuid.uuid4()

        while Session.objects.filter(uuid=session_uuid).count() > 0:
            session_uuid = uuid.uuid4()

        url = self.session_detail_endpoint.format(uuid=session_uuid)

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
