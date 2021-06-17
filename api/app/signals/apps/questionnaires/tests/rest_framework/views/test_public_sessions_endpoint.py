# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import os

from django.test import override_settings
from django.urls import include, path
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.questionnaires.factories import QuestionnaireFactory, SessionFactory
from signals.apps.questionnaires.tests.mixin import ValidateJsonSchemaMixin

THIS_DIR = os.path.dirname(__file__)


urlpatterns = [
    path('', include(('signals.apps.questionnaires.urls', 'signals.apps.questionnaires'), namespace='v1')),
]


class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns


@override_settings(ROOT_URLCONF=test_urlconf)
class TestPublicSessionEndpoint(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/public/qa/sessions/'

    def setUp(self):
        self.questionnaire = QuestionnaireFactory.create()
        self.session = SessionFactory.create(questionnaire=self.questionnaire)

        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../json_schema/public_get_session_detail.json')
        )

    def test_session_detail(self):
        response = self.client.get(f'{self.base_endpoint}{self.session.uuid}')
        self.assertEqual(response.status_code, 200)

        self.assertJsonSchema(self.detail_schema, response.json())

    def test_session_detail_gone(self):
        now = timezone.now()
        with freeze_time(now - timezone.timedelta(days=1)):
            session = SessionFactory.create(questionnaire=self.questionnaire)

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 410)

        now = timezone.now()
        with freeze_time(now - timezone.timedelta(days=1)):
            session = SessionFactory.create(questionnaire=self.questionnaire,
                                            submit_before=now-timezone.timedelta(hours=1))

        response = self.client.get(f'{self.base_endpoint}{session.uuid}')
        self.assertEqual(response.status_code, 410)

    def test_session_list_not_found(self):
        response = self.client.get(f'{self.base_endpoint}')
        self.assertEqual(response.status_code, 404)

    def test_session_create_not_found(self):
        response = self.client.post(f'{self.base_endpoint}', data={})
        self.assertEqual(response.status_code, 404)

    def test_session_update_not_allowed(self):
        response = self.client.patch(f'{self.base_endpoint}{self.questionnaire.uuid}', data={})
        self.assertEqual(response.status_code, 405)

    def test_session_delete_not_allowed(self):
        response = self.client.delete(f'{self.base_endpoint}{self.questionnaire.uuid}')
        self.assertEqual(response.status_code, 405)
