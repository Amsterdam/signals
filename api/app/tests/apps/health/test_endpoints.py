from django.test import TestCase

from tests.apps.signals.factories import SignalFactory


class TestHealthEndpoints(TestCase):

    def test_status_health(self):
        response = self.client.get('/status/health')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'Connectivity OK')

    def test_status_data_success(self):
        # We need two Signal objects.
        SignalFactory.create()
        SignalFactory.create()

        response = self.client.get('/status/data')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'Data OK 2 Signal')

    def test_status_data_failed(self):
        response = self.client.get('/status/data')

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b'Too few items in the database')
