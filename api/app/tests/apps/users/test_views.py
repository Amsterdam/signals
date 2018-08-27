import json

from rest_framework.test import APITestCase


class TestUserMeView(APITestCase):

    def test_get(self):
        response = self.client.get('/signals/user/auth/me/')

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        self.assertEqual(json_data['username'], 'signals.admin@amsterdam.nl')
        self.assertEqual(json_data['is_staff'], True)
        self.assertEqual(json_data['is_superuser'], True)
