from rest_framework import status

from tests.test import SignalsBaseApiTestCase


class TestPrivateSignalEndpointUnAuthorized(SignalsBaseApiTestCase):
    def test_list_endpoint(self):
        response = self.client.get('/signals/v1/private/signals/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_endpoint(self):
        response = self.client.get('/signals/v1/private/signals/1')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_endpoint(self):
        response = self.client.post('/signals/v1/private/signals/1', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_endpoint(self):
        response = self.client.put('/signals/v1/private/signals/1', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.patch('/signals/v1/private/signals/1', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_endpoint(self):
        response = self.client.delete('/signals/v1/private/signals/1')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
