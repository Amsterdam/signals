from django.contrib.auth.models import Permission
from rest_framework import status

from signals.apps.signals.factories import (
    ExpressionContextFactory,
    ExpressionFactory,
    ExpressionTypeFactory
)
from signals.apps.signals.models import ExpressionContext
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestPrivateExpressionEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    list_endpoint = '/signals/v1/private/expressions/'
    detail_endpoint = '/signals/v1/private/expressions/{pk}'

    def setUp(self):
        self.expression_read = Permission.objects.get(
            codename='sia_expression_read'
        )
        self.expression_write = Permission.objects.get(
            codename='sia_expression_write'
        )
        self.sia_read_write_user.user_permissions.add(self.expression_read)
        self.sia_read_write_user.user_permissions.add(self.expression_write)

        self.exp_routing_type = ExpressionTypeFactory.create(name="routing")
        self.exp_int_id = ExpressionContextFactory.create(
            _type=self.exp_routing_type,
            identifier_type=ExpressionContext.CTX_NUMBER
        )
        self.exp_str_id = ExpressionContextFactory.create(
            _type=self.exp_routing_type,
            identifier_type=ExpressionContext.CTX_STRING
        )
        self.sample_int_expr = ExpressionFactory.create(
            _type=self.exp_routing_type,
            code="{} > 1".format(self.exp_int_id.identifier)
        )

    def _create_expression(self, name):
        data = {
            'name': name,
            'code': '{} == "test"'.format(self.exp_str_id.identifier),
            'type': self.exp_routing_type.name
        }

        response = self.client.post(
            self.list_endpoint, data=data, format='json'
        )
        return response

    def test_get_list_context(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get(self.list_endpoint + 'context/?type={}'.format(self.exp_routing_type.name))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 2)

    def test_get_list(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['results']), 1)

    def test_get_detail(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get(self.detail_endpoint.format(pk=self.sample_int_expr.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['name'], self.sample_int_expr.name)
        self.assertEqual(data['code'], self.sample_int_expr.code)
        self.assertEqual(data['type'], self.sample_int_expr._type.name)

    def test_post(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self._create_expression(name='test exp')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data['name'], 'test exp')
        self.assertEqual(data['code'], '{} == "test"'.format(self.exp_str_id.identifier))
        self.assertEqual(data['type'], self.exp_routing_type.name)

    def test_patch(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self._create_expression(name='test patch ok exp')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pk = response.json()['id']

        data = {
            'name': 'new name',
            'code': '{} >= 10'.format(self.exp_int_id.identifier),
            'type': self.exp_routing_type.name
        }

        response = self.client.patch(
            self.detail_endpoint.format(pk=pk), data=data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['name'], 'new name')
        self.assertEqual(data['code'], '{} >= 10'.format(self.exp_int_id.identifier))
        self.assertEqual(data['type'], self.exp_routing_type.name)

    def test_patch_invalid_data(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self._create_expression(name='test patch error exp')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pk = response.json()['id']

        data = {
            'name': 'blabla',
            'code': '{} >= 10'.format(self.exp_int_id.identifier),
            'type': 'bogus type'
        }

        response = self.client.patch(
            self.detail_endpoint.format(pk=pk), data=data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data['non_field_errors'][0], 'type: bogus type does not exists')

    def test_delete(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.delete(self.detail_endpoint.format(pk=self.exp_int_id.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_validate_expression(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        expr = "{} > 100".format(self.exp_int_id.identifier)
        param = 'validate/?expression={e}&type={t}'.format(t=self.exp_routing_type.name, e=expr)
        response = self.client.get(self.list_endpoint + param)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_validate_expression_unknown_ident(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        expr = "abcd > 100"
        param = 'validate/?expression={e}&type={t}'.format(t=self.exp_routing_type.name, e=expr)
        response = self.client.get(self.list_endpoint + param)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validate_expression_syntax_error(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        expr = "{} >< 100".format(self.exp_int_id.identifier)
        param = 'validate/?expression={e}&type={t}'.format(t=self.exp_routing_type.name, e=expr)
        response = self.client.get(self.list_endpoint + param)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
