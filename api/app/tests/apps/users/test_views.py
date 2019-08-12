from django.contrib.auth.models import Group

from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestUserMeView(SIAReadWriteUserMixin, SignalsBaseApiTestCase):

    def test_get_authenticated_superuser(self):
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

    def test_get_authenticated_readwriteuser(self):
        department_group = Group.objects.create(name='dep_group')
        self.sia_read_write_user.groups.add(department_group)

        normal_group = Group.objects.create(name='just-a-group')
        self.sia_read_write_user.groups.add(normal_group)

        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get('/signals/user/auth/me/')

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['email'], self.sia_read_write_user.email)
        self.assertEqual(json_data['username'], self.sia_read_write_user.username)
        self.assertEqual(json_data['is_superuser'], False)
        self.assertEqual(json_data['is_staff'], False)

        # check for some known signals.apps.signals permissions
        self.assertIn('signals.sia_read', json_data['permissions'])
        self.assertIn('signals.sia_write', json_data['permissions'])

    def test_get_unauthenticated(self):
        response = self.client.get('/signals/user/auth/me/')

        self.assertEqual(response.status_code, 401)
