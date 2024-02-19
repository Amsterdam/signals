# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2024 Gemeente Amsterdam
from unittest import mock

from rest_framework.status import HTTP_503_SERVICE_UNAVAILABLE
from rest_framework.test import APITestCase


class TestMaintenanceMode(APITestCase):
    endpoints: list[str] = [
        '/signals/v1/',
        '/signals/v1/public/terms/categories/',
        '/signals/v1/private/categories/',
        '/signals/v1/private/signals/',
        '/signals/v1/private/status-messages/',
    ]

    @mock.patch.dict('os.environ', {'MAINTENANCE_MODE': 'True'}, clear=True)
    def test_maintenance_mode_enabled(self):
        for endpoint in self.endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, HTTP_503_SERVICE_UNAVAILABLE)

    @mock.patch.dict('os.environ', {'MAINTENANCE_MODE': 'False'}, clear=True)
    def test_maintenance_mode_disabled(self):
        for endpoint in self.endpoints:
            response = self.client.get(endpoint)
            self.assertNotEqual(response.status_code, HTTP_503_SERVICE_UNAVAILABLE)
