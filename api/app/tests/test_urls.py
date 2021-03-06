# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from django.test import TestCase


class TestURLs(TestCase):

    def test_swagger_index(self):
        url = '/signals/swagger/openapi.yaml'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
