import json

from rest_framework.test import APITestCase

from tests.apps.users.factories import SuperUserFactory


class TestUserMeView(APITestCase):

    def test_get_authenticated(self):
        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)
        response = self.client.get('/signals/user/auth/me/')

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        self.assertEqual(json_data['email'], 'signals.admin@amsterdam.nl')
        self.assertEqual(json_data['username'], 'signals.admin@amsterdam.nl')
        self.assertEqual(json_data['is_superuser'], True)
        self.assertEqual(json_data['is_staff'], True)

    def test_get_unauthenticated(self):
        response = self.client.get('/signals/user/auth/me/')

        self.assertEqual(response.status_code, 401)
