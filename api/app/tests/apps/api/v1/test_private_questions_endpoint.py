from django.contrib.auth.models import Permission
from rest_framework import status

from signals.apps.signals.factories import QuestionFactory
from signals.apps.signals.models import Question
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestPrivateExpressionEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    list_endpoint = '/signals/v1/private/questions/'
    detail_endpoint = '/signals/v1/private/questions/{pk}/'

    def setUp(self):
        self.questions_read = Permission.objects.get(
            codename='sia_question_read'
        )
        self.questions_write = Permission.objects.get(
            codename='sia_question_write'
        )
        self.sia_read_write_user.user_permissions.add(self.questions_read)
        self.sia_read_write_user.user_permissions.add(self.questions_write)

        self.question = QuestionFactory.create()

    def _create_question(self, key, field_type, required):
        data = {
            'key': key,
            'field_type': field_type,
            'required': required,
            'meta': {
                'label': 'test question',
                'values': {
                    'key': 'value'
                }
            }
        }

        response = self.client.post(
            self.list_endpoint, data=data, format='json'
        )
        return response

    def test_get_detail(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(self.detail_endpoint.format(pk=self.question.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self._create_question(
            key='testkey',
            field_type=Question.PLAIN_TEXT,
            required=True
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_patch(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'key': 'newkey',
            'field_type': Question.MULTI_TEXT_INPUT,
            'required': False,
            'meta': {
                'label': 'test question',
                'values': {
                    'key': 'value'
                }
            }
        }

        response = self.client.patch(
            self.detail_endpoint.format(pk=self.question.pk), data=data, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['key'], 'newkey')
        self.assertEqual(data['field_type'], Question.MULTI_TEXT_INPUT)
        self.assertFalse(data['required'])

    def test_delete(self):
        pk = self.question.pk
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.delete(self.detail_endpoint.format(pk=pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(self.detail_endpoint.format(pk=pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
