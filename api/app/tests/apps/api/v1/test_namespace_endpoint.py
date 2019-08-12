from tests.test import SignalsBaseApiTestCase


class TestNamespaceEndpoint(SignalsBaseApiTestCase):
    endpoint = '/signals/v1/relations'

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)

    def test_not_allowed(self):
        response = self.client.post(self.endpoint, {})
        self.assertEqual(response.status_code, 405)

        response = self.client.put(self.endpoint, {})
        self.assertEqual(response.status_code, 405)

        response = self.client.patch(self.endpoint, {})
        self.assertEqual(response.status_code, 405)

        response = self.client.delete(self.endpoint)
        self.assertEqual(response.status_code, 405)
