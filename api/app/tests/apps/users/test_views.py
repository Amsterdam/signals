from django.contrib.auth.models import Group
from django.test import override_settings
from django.urls import path
from rest_framework import status

from signals.apps.users.v0.views import UserMeView
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


# V0 has been disabled but we still want to test the code, so for the tests we will add the endpoints
class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = [
    path('signals/auth/me/', UserMeView.as_view()),
    path('signals/user/auth/me/', UserMeView.as_view()),
]


@override_settings(ROOT_URLCONF=test_urlconf)
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

    def test_history_view(self):
        self.client.force_authenticate(user=self.superuser)

        group = Group.objects.create(name='Test group')

        url = f'/signals/v1/private/users/{self.superuser.pk}'

        response = self.client.patch(url, data={'first_name': 'Patched', 'role_ids': [group.pk]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(url, data={'last_name': 'Patched', 'is_active': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        history_url = f'{url}/history'
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(len(response_data), 2)

        change_log_data = response_data[0]
        self.assertEqual(change_log_data['what'], 'UPDATED_USER')
        self.assertEqual(change_log_data['who'], self.superuser.username)
        self.assertIn('Achternaam gewijzigd:\n Patched', change_log_data['action'])
        self.assertIn('Status wijziging:\n Inactief', change_log_data['action'])

        change_log_data = response_data[1]
        self.assertEqual(change_log_data['what'], 'UPDATED_USER')
        self.assertEqual(change_log_data['who'], self.superuser.username)
        self.assertIn('Voornaam gewijzigd:\n Patched', change_log_data['action'])
        self.assertIn(f'Rol wijziging:\n {group.name}', change_log_data['action'])
