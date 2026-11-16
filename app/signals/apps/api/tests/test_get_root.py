# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from rest_framework.test import APITestCase


class TestGetRoot(APITestCase):
    api_root = '/signals/'

    def test_get_root(self):
        result = self.client.get(self.api_root)
        self.assertEqual(result.status_code, 200)

    def test_browsable_api_has_content_security_policy(self):
        response = self.client.get(self.api_root, HTTP_ACCEPT='text/html')

        self.assertEqual(response.status_code, 200)
        self.assertIn("default-src 'self'", response['Content-Security-Policy'])
