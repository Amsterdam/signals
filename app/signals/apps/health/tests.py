# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from unittest import mock

from django.db import Error
from django.test import TestCase
from rest_framework.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR


class TestHealthEndpoint(TestCase):
    endpoint = '/status/health'

    def test_get_200(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(HTTP_200_OK, response.status_code)

    @mock.patch('signals.apps.health.views.connections')
    def test_get_500(self, mocked_connections):
        mocked_connections.__getitem__.return_value.cursor.side_effect = Error('Database connection error')

        response = self.client.get(self.endpoint)
        self.assertEqual(HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)
        self.assertEqual(response.content, b'Database connectivity failed')
