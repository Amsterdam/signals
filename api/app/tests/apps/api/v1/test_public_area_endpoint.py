from rest_framework import status

from tests.apps.signals.factories import AreaFactory, AreaTypeFactory
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestPublicAreaEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    list_endpoint = '/signals/v1/public/areas/'

    def setUp(self):
        super(TestPublicAreaEndpoint, self).setUp()

        self.areas = {}
        self.area_types = AreaTypeFactory.create_batch(5)
        for area_type in self.area_types:
            self.areas[area_type.code] = AreaFactory.create_batch(5, _type=area_type)

    def test_get_list(self):
        response = self.client.get(self.list_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(25, len(data['features']))

    def test_get_list_filter(self):
        response = self.client.get(f'{self.list_endpoint}?type_code={self.area_types[0].code}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(5, len(data['features']))

    def test_get_list_multiple_filter(self):
        response = self.client.get(f'{self.list_endpoint}?type_code={self.area_types[0].code}'
                                   f'&type_code={self.area_types[1].code}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(10, len(data['features']))

    def test_get_detail(self):
        response = self.client.get(f'{self.list_endpoint}{self.areas[self.area_types[0].code][0].id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_method_not_allowed(self):
        response = self.client.post(f'{self.list_endpoint}1', data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_method_not_allowed(self):
        response = self.client.patch(f'{self.list_endpoint}1', data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_method_not_allowed(self):
        response = self.client.delete(f'{self.list_endpoint}1')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
