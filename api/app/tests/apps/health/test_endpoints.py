from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.db import Error
from django.test import TestCase, override_settings

from tests.apps.signals.factories import SignalFactory


class TestHealthEndpoints(TestCase):

    def test_status_health_success(self):
        response = self.client.get('/status/health')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'Connectivity OK')

    @mock.patch('signals.apps.health.views.connection')
    def test_status_health_failed(self, mocked_connection):
        mocked_cursor = mock.MagicMock()
        mocked_cursor.execute.side_effect = Error()
        mocked_connection.cursor.return_value.__enter__.return_value = mocked_cursor

        response = self.client.get('/status/health')

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b'Database connectivity failed')

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

    def test_status_data_categories_success(self):
        response = self.client.get('/status/data/categories')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'Data OK Category')

    @override_settings(HEALTH_MODEL='signals.THIS_MODEL_DOES_NOT_EXISTS')
    def test_status_data_lookup_error(self):
        with self.assertRaises(ImproperlyConfigured):
            self.client.get('/status/data')
