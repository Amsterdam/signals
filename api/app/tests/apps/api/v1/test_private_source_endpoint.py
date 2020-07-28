import os

from rest_framework import status

from tests.apps.signals.factories import SourceFactory
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)


class TestPrivateSourceEndpointUnAuthorized(SignalsBaseApiTestCase):
    def test_list_endpoint(self):
        response = self.client.get('/signals/v1/private/signals/')
        self.assertEqual(response.status_code, 401)


class TestPrivateSourceEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    list_endpoint = '/signals/v1/private/sources/'

    def setUp(self):
        super(TestPrivateSourceEndpoint, self).setUp()
        self.client.force_authenticate(user=self.sia_read_write_user)

        self.sources = SourceFactory.create_batch(5)

        self.list_sources_schema = self.load_json_schema(
            os.path.join(THIS_DIR, 'json_schema', 'get_signals_v1_private_sources.json')
        )

    def test_get_list(self):
        response = self.client.get(f'{self.list_endpoint}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(5, data['count'])
        self.assertEqual(5, len(data['results']))
        self.assertJsonSchema(self.list_sources_schema, data)

    def test_post_method_not_allowed(self):
        response = self.client.post(f'{self.list_endpoint}1', data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_method_not_allowed(self):
        response = self.client.patch(f'{self.list_endpoint}1', data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_method_not_allowed(self):
        response = self.client.delete(f'{self.list_endpoint}1')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
