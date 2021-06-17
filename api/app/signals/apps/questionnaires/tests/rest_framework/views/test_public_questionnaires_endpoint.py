# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import os

from django.test import override_settings
from django.urls import include, path
from rest_framework.test import APITestCase

from signals.apps.questionnaires.factories import QuestionnaireFactory
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
class TestPublicQuestionnaireEndpoint(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/public/qa/questionnaires/'

    def setUp(self):
        self.skipTest('must be ported to new Question model')
        self.questionnaire = QuestionnaireFactory.create()

        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../json_schema/public_get_questionnaire_detail.json')
        )
        self.list_schema = self.load_json_schema(
            os.path.join(THIS_DIR, '../json_schema/public_get_questionnaire_list.json')
        )

    def test_questionnaire_list(self):
        response = self.client.get(f'{self.base_endpoint}')
        self.assertEqual(response.status_code, 200)

        self.assertJsonSchema(self.list_schema, response.json())

    def test_questionnaire_detail_by_key(self):
        response = self.client.get(f'{self.base_endpoint}{self.questionnaire.uuid}')
        self.assertEqual(response.status_code, 200)

        self.assertJsonSchema(self.detail_schema, response.json())

    def test_questionnaire_detail_by_uuid(self):
        response = self.client.get(f'{self.base_endpoint}{self.questionnaire.uuid}')
        self.assertEqual(response.status_code, 200)

        self.assertJsonSchema(self.detail_schema, response.json())

    def test_questionnaire_create_not_allowed(self):
        response = self.client.post(f'{self.base_endpoint}', data={})
        self.assertEqual(response.status_code, 405)

    def test_questionnaire_update_not_allowed(self):
        response = self.client.patch(f'{self.base_endpoint}{self.questionnaire.uuid}', data={})
        self.assertEqual(response.status_code, 405)

    def test_questionnaire_delete_not_allowed(self):
        response = self.client.delete(f'{self.base_endpoint}{self.questionnaire.uuid}')
        self.assertEqual(response.status_code, 405)
