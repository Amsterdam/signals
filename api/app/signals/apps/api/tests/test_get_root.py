# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from rest_framework.test import APITestCase


class TestGetRoot(APITestCase):
    api_root = '/signals/'

    def test_get_root(self):
        result = self.client.get(self.api_root)
        self.assertEqual(result.status_code, 200)
