from tests.test import SignalsBaseApiTestCase


class TestUserMeView(SignalsBaseApiTestCase):

    def test_get_authenticated(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/signals/user/auth/me/')

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['email'], self.superuser.email)
        self.assertEqual(json_data['username'], self.superuser.username)
        self.assertEqual(json_data['is_superuser'], True)
        self.assertEqual(json_data['is_staff'], True)

        # check for some known signals.apps.signals permissions
        self.assertIn('signals.add_signal', json_data['permissions'])
        self.assertIn('signals.add_status', json_data['permissions'])

    def test_get_unauthenticated(self):
        response = self.client.get('/signals/user/auth/me/')

        self.assertEqual(response.status_code, 401)
