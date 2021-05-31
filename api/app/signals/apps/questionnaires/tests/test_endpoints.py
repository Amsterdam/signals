# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import os

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import include, path
from rest_framework.test import APITestCase

from signals.apps.questionnaires.models import Question, Questionnaire
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
    base_endpoint = '/public/questionnaires/'

    def setUp(self):
        self.questionnaire = Questionnaire.objects.create()

        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema/public_get_questionnaire_detail.json')
        )
        self.list_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema/public_get_questionnaire_list.json')
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


@override_settings(ROOT_URLCONF=test_urlconf)
class TestPrivateQuestionnaireEndpoint(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/private/questionnaires/'

    def setUp(self):
        user_model = get_user_model()
        self.superuser, _ = user_model.objects.get_or_create(
            email='signals.admin@example.com', is_superuser=True,
            defaults={'first_name': 'John', 'last_name': 'Doe', 'is_staff': True}
        )
        self.questionnaire = Questionnaire.objects.create()

        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema/private_get_questionnaire_detail.json')
        )
        self.list_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema/private_get_questionnaire_list.json')
        )

    def test_questionnaire_list(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(f'{self.base_endpoint}')
        self.assertEqual(response.status_code, 200)

        self.assertJsonSchema(self.list_schema, response.json())

        self.client.logout()

    def test_questionnaire_detail(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(f'{self.base_endpoint}{self.questionnaire.id}')
        self.assertEqual(response.status_code, 200)

        self.assertJsonSchema(self.detail_schema, response.json())

        self.client.logout()

    def test_questionnaire_list_unauthorized(self):
        response = self.client.get(f'{self.base_endpoint}')
        self.assertEqual(response.status_code, 401)

    def test_questionnaire_detail_unauthorized(self):
        response = self.client.get(f'{self.base_endpoint}{self.questionnaire.id}')
        self.assertEqual(response.status_code, 401)

    def test_questionnaire_create_unauthorized(self):
        response = self.client.post(f'{self.base_endpoint}', data={})
        self.assertEqual(response.status_code, 401)

    def test_questionnaire_update_unauthorized(self):
        response = self.client.patch(f'{self.base_endpoint}{self.questionnaire.id}', data={})
        self.assertEqual(response.status_code, 401)

    def test_questionnaire_delete_unauthorized(self):
        response = self.client.delete(f'{self.base_endpoint}{self.questionnaire.id}')
        self.assertEqual(response.status_code, 401)

    def test_questionnaire_create_not_allowed(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.post(f'{self.base_endpoint}', data={})
        self.assertEqual(response.status_code, 405)

        self.client.logout()

    def test_questionnaire_update_not_allowed(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.patch(f'{self.base_endpoint}{self.questionnaire.id}', data={})
        self.assertEqual(response.status_code, 405)

        self.client.logout()

    def test_questionnaire_delete_not_allowed(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.delete(f'{self.base_endpoint}{self.questionnaire.id}')
        self.assertEqual(response.status_code, 405)

        self.client.logout()


@override_settings(ROOT_URLCONF=test_urlconf)
class TestPublicQuestionEndpoint(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/public/question/'

    def setUp(self):
        self.question, _ = Question.objects.get_or_create(key='test')

        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema/public_get_question_detail.json')
        )
        self.list_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema/public_get_question_list.json')
        )

    def test_question_list(self):
        response = self.client.get(f'{self.base_endpoint}')
        self.assertEqual(response.status_code, 200)

        self.assertJsonSchema(self.list_schema, response.json())

    def test_question_detail(self):
        response = self.client.get(f'{self.base_endpoint}{self.question.uuid}')
        self.assertEqual(response.status_code, 200)

        self.assertJsonSchema(self.detail_schema, response.json())

    def test_question_create_not_allowed(self):
        response = self.client.post(f'{self.base_endpoint}', data={})
        self.assertEqual(response.status_code, 405)

    def test_question_update_not_allowed(self):
        response = self.client.patch(f'{self.base_endpoint}{self.question.uuid}', data={})
        self.assertEqual(response.status_code, 405)

    def test_question_delete_not_allowed(self):
        response = self.client.delete(f'{self.base_endpoint}{self.question.uuid}')
        self.assertEqual(response.status_code, 405)


@override_settings(ROOT_URLCONF=test_urlconf)
class TestPrivateQuestionEndpoint(ValidateJsonSchemaMixin, APITestCase):
    base_endpoint = '/private/question/'

    def setUp(self):
        user_model = get_user_model()
        self.superuser, _ = user_model.objects.get_or_create(
            email='signals.admin@example.com', is_superuser=True,
            defaults={'first_name': 'John', 'last_name': 'Doe', 'is_staff': True}
        )
        self.question, _ = Question.objects.get_or_create(key='test')

        self.detail_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema/private_get_question_detail.json')
        )
        self.list_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema/private_get_question_list.json')
        )

    def test_question_list(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(f'{self.base_endpoint}')
        self.assertEqual(response.status_code, 200)

        self.assertJsonSchema(self.list_schema, response.json())

        self.client.logout()

    def test_question_detail(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(f'{self.base_endpoint}{self.question.id}')
        self.assertEqual(response.status_code, 200)

        self.assertJsonSchema(self.detail_schema, response.json())

        self.client.logout()

    def test_question_list_unauthorized(self):
        response = self.client.get(f'{self.base_endpoint}')
        self.assertEqual(response.status_code, 401)

    def test_question_detail_unauthorized(self):
        response = self.client.get(f'{self.base_endpoint}{self.question.id}')
        self.assertEqual(response.status_code, 401)

    def test_question_create_unauthorized(self):
        response = self.client.post(f'{self.base_endpoint}', data={})
        self.assertEqual(response.status_code, 401)

    def test_question_update_unauthorized(self):
        response = self.client.patch(f'{self.base_endpoint}{self.question.id}', data={})
        self.assertEqual(response.status_code, 401)

    def test_question_delete_unauthorized(self):
        response = self.client.delete(f'{self.base_endpoint}{self.question.id}')
        self.assertEqual(response.status_code, 401)

    def test_question_create_not_allowed(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.post(f'{self.base_endpoint}', data={})
        self.assertEqual(response.status_code, 405)

        self.client.logout()

    def test_question_update_not_allowed(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.patch(f'{self.base_endpoint}{self.question.id}', data={})
        self.assertEqual(response.status_code, 405)

        self.client.logout()

    def test_question_delete_not_allowed(self):
        self.client.force_authenticate(user=self.superuser)

        response = self.client.delete(f'{self.base_endpoint}{self.question.id}')
        self.assertEqual(response.status_code, 405)

        self.client.logout()
