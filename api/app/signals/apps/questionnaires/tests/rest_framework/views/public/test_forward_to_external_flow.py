# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
"""
Test the forward to external flow at REST API level.
"""
import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.test import override_settings
from django.urls import include, path
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.api.views import NamespaceView
from signals.apps.questionnaires.app_settings import FORWARD_TO_EXTERNAL_DAYS_OPEN
from signals.apps.signals.factories import SignalFactory, StatusFactory
from signals.apps.questionnaires.factories import AnswerFactory
from signals.apps.questionnaires.models import Questionnaire, Session
from signals.apps.questionnaires.services.forward_to_external import create_session_for_forward_to_external
from signals.apps.questionnaires.tests.mixin import ValidateJsonSchemaMixin
from signals.apps.signals import workflow


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
class TestForwardToExternal(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/public/qa/questions/'
    session_detail_endpoint = '/public/qa/sessions/{uuid}/'
    question_detail_endpoint = '/public/qa/questions/{ref}'

    def setUp(self):
        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_get_question_detail.json')
        )
        self.list_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_get_question_list.json')
        )
        self.post_answer_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_post_question_answer_response.json')
        )
        self.session_detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../../json_schema/public_get_session_detail.json')
        )

        self.t_creation = datetime(2021, 10, 1, 0, 0, 0)
        # self.t_answer_in_time = self.t_creation + relativedelta(days=FORWARD_TO_EXTERNAL_DAYS_OPEN / 2)
        # self.t_answer_too_late = self.t_creation + relativedelta(days=FORWARD_TO_EXTERNAL_DAYS_OPEN * 2)
        seconds_open = FORWARD_TO_EXTERNAL_DAYS_OPEN * 24 * 60 * 60
        self.t_answer_in_time = self.t_creation + timedelta(seconds=seconds_open / 2)
        self.t_answer_too_late = self.t_creation + timedelta(seconds=seconds_open * 2)

        with freeze_time(self.t_creation):
            self.signal = SignalFactory.create(
                created_at=self.t_creation,
                status__state=workflow.DOORZETTEN_NAAR_EXTERN,
                status__text='SOME QUESTION',
                status__email_override='a@example.com'
            )
            self.session = create_session_for_forward_to_external(self.signal)

        self.assertIsInstance(self.session, Session)
        self.assertEqual(self.session.questionnaire.flow, Questionnaire.FORWARD_TO_EXTERNAL)
        self.assertEqual(self.session._signal.status.state, workflow.DOORZETTEN_NAAR_EXTERN)

        self.session_url = self.session_detail_endpoint.format(uuid=str(self.session.uuid))  # fstring here

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

    @patch('signals.apps.questionnaires.rest_framework.fields.SessionPublicHyperlinkedIdentityField.get_url',
           autospec=True)
    def test_retrieve_session_forward_to_external_several_open(self, patched_get_url):
        """
        Forward to external flow can have several sessions open at once, all of
        which can be retrieved.
        """
        patched_get_url.return_value = '/some/url/'

        old_session_url = self.session_url
        with freeze_time(self.t_creation + timedelta(seconds = 60 * 60 * 24)):
            new_status = StatusFactory.create(
                state=workflow.DOORZETTEN_NAAR_EXTERN,
                text='SOME SECOND QUESTION',
                email_override='b@example.com',
            )
            self.signal.status = new_status
            self.signal.save()
        new_session = create_session_for_forward_to_external(self.signal)
        new_session_url = self.session_detail_endpoint.format(uuid=str(new_session.uuid))

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(old_session_url)
        self.assertEqual(response.status_code, 200)

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(new_session_url)
        self.assertEqual(response.status_code, 200)

    @patch('signals.apps.questionnaires.rest_framework.fields.SessionPublicHyperlinkedIdentityField.get_url',
           autospec=True)
    def test_retrieve_session_signal_state_not_DOORZETTEN_NAAR_EXTERN(self, patched_get_url):
        """
        Forward to external flow will not "close" open sessions when the status
        of the associated Signal changes to something other than
        DOORZETTEN_NAAR_EXTERN.
        """
        patched_get_url.return_value = '/some/url/'

        with freeze_time(self.t_creation + timedelta(seconds = 60 * 60 * 24)):
            new_status = StatusFactory.create(state=workflow.BEHANDELING, text='We are busy.')
            self.signal.status = new_status
            self.signal.save()

        with freeze_time(self.t_answer_in_time):
            response = self.client.get(self.session_url)

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
