import unittest

from django.contrib.auth.models import Group, Permission

from tests.apps.signals.factories import DepartmentFactory
from tests.apps.users.factories import GroupFactory
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestUsersViews(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        permission = Permission.objects.get(codename='view_user')
        self.sia_read_write_user.user_permissions.add(permission)

        permission = Permission.objects.get(codename='add_user')
        self.sia_read_write_user.user_permissions.add(permission)

        permission = Permission.objects.get(codename='change_user')
        self.sia_read_write_user.user_permissions.add(permission)

        self.group_with_permissions = GroupFactory.create(name='This group does have permissions')
        self.group_with_permissions.permissions.add(self.sia_write)

        self.departments = DepartmentFactory.create_batch(5)

    def test_get_users(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get('/signals/v1/private/users/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['results']), 1)

        response_data = data['results'][0]
        self.assertEqual(response_data['id'], self.sia_read_write_user.pk)
        self.assertEqual(response_data['username'], self.sia_read_write_user.username)
        self.assertTrue(response_data['is_active'])
        self.assertEqual(len(response_data['roles']), 1)

    def test_get_user(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get('/signals/v1/private/users/{}'.format(
            self.sia_read_write_user.pk
        ))
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['id'], self.sia_read_write_user.pk)
        self.assertEqual(response_data['username'], self.sia_read_write_user.username)
        self.assertEqual(response_data['email'], self.sia_read_write_user.email)
        self.assertTrue(response_data['is_active'])
        self.assertFalse(response_data['is_staff'])
        self.assertFalse(response_data['is_superuser'])
        self.assertEqual(len(response_data['roles']), 1)
        self.assertEqual(len(response_data['permissions']), 5)

    def test_get_users_not_authenticated(self):
        response = self.client.get('/signals/v1/private/users/')
        self.assertEqual(response.status_code, 401)

    def test_post_users(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'username': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'Tester',
            'is_active': True,
            'role_ids': [self.group_with_permissions.pk, ],
        }

        response = self.client.post('/signals/v1/private/users/', data=data, format='json')
        self.assertEqual(response.status_code, 201)

        response_data = response.json()

        self.assertIsNotNone(response_data['id'])
        self.assertEqual(response_data['username'], data['username'])
        self.assertEqual(response_data['email'], data['username'])
        self.assertEqual(response_data['first_name'], data['first_name'])
        self.assertEqual(response_data['last_name'], data['last_name'])
        self.assertTrue(response_data['is_active'])
        self.assertFalse(response_data['is_staff'])
        self.assertFalse(response_data['is_superuser'])

        self.assertEqual(len(response_data['roles']), 1)
        role_data = response_data['roles'][0]
        self.assertEqual(role_data['permissions'][0]['id'], self.sia_write.pk)
        self.assertEqual(role_data['permissions'][0]['name'], self.sia_write.name)
        self.assertEqual(role_data['permissions'][0]['codename'], self.sia_write.codename)

    def test_post_user_profile(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'username': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'Tester',
            'is_active': True,
            'role_ids': [self.group_with_permissions.pk, ],
            'profile': {
                'department_ids': [self.departments[0].pk, self.departments[1].pk, ],
                'note': 'This is a test note'
            }
        }

        response = self.client.post('/signals/v1/private/users/', data=data, format='json')
        self.assertEqual(response.status_code, 201)

        response_data = response.json()

        self.assertIsNotNone(response_data['id'])
        self.assertEqual(response_data['username'], data['username'])
        self.assertEqual(response_data['email'], data['username'])
        self.assertEqual(response_data['first_name'], data['first_name'])
        self.assertEqual(response_data['last_name'], data['last_name'])
        self.assertTrue(response_data['is_active'])
        self.assertFalse(response_data['is_staff'])
        self.assertFalse(response_data['is_superuser'])

        self.assertEqual(len(response_data['roles']), 1)
        role_data = response_data['roles'][0]
        self.assertEqual(role_data['permissions'][0]['id'], self.sia_write.pk)
        self.assertEqual(role_data['permissions'][0]['name'], self.sia_write.name)
        self.assertEqual(role_data['permissions'][0]['codename'], self.sia_write.codename)

        self.assertEqual(len(response_data['permissions']), 0)

        self.assertEqual(response_data['profile']['note'], 'This is a test note')
        self.assertEqual(len(response_data['profile']['departments']), 2)
        self.assertIn(response_data['profile']['departments'][0],
                      [self.departments[0].name, self.departments[1].name])
        self.assertIn(response_data['profile']['departments'][1],
                      [self.departments[0].name, self.departments[1].name])

    def test_post_users_invalid_data(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'username': 'this is not an email address',
            'is_active': 'not a boolean',
            'role_ids': [666666, ],  # non existing role
        }

        response = self.client.post('/signals/v1/private/users/', data=data, format='json')
        self.assertEqual(response.status_code, 400)

        response_data = response.json()
        self.assertEqual(len(response_data), 3)
        self.assertIsNotNone('username', response_data)
        self.assertIsNotNone('is_active', response_data)
        self.assertIsNotNone('role_ids', response_data)

        self.assertEqual(response_data['username'][0], 'Voer een geldig e-mailadres in.')
        self.assertEqual(response_data['is_active'][0], 'Must be a valid boolean.')

    def test_patch_user(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'username': 'this.is.the.new.address@test.com',
            'is_active': False,
            'profile': {
                'department_ids': [self.departments[0].pk, self.departments[1].pk, ],
            }
        }

        response = self.client.patch('/signals/v1/private/users/{}'.format(
            self.sia_read_write_user.pk
        ), data=data, format='json')
        self.assertEqual(response.status_code, 200)

        self.sia_read_write_user.refresh_from_db()

        response_data = response.json()
        self.assertEqual(response_data['username'], self.sia_read_write_user.username)
        self.assertNotEqual(response_data['username'], 'this.is.the.new.address@test.com')
        self.assertEqual(response_data['email'], self.sia_read_write_user.email)
        self.assertEqual(response_data['first_name'], self.sia_read_write_user.first_name)
        self.assertEqual(response_data['last_name'], self.sia_read_write_user.last_name)
        self.assertFalse(response_data['is_active'])
        self.assertEqual(len(response_data['permissions']), 5)
        self.assertEqual(len(response_data['profile']['departments']), 2)
        self.assertIn(response_data['profile']['departments'][0],
                      [self.departments[0].name, self.departments[1].name])
        self.assertIn(response_data['profile']['departments'][1],
                      [self.departments[0].name, self.departments[1].name])

    def test_patch_user_note(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {'profile': {'note': 'note #1'}}
        response = self.client.patch('/signals/v1/private/users/{}'.format(
            self.sia_read_write_user.pk
        ), data=data, format='json')
        self.assertEqual(response.status_code, 200)

        self.sia_read_write_user.refresh_from_db()
        self.assertEqual(self.sia_read_write_user.profile.note, 'note #1')

        response_data = response.json()
        self.assertEqual(response_data['profile']['note'], 'note #1')

        data = {'profile': {'note': 'note #2'}}
        response = self.client.patch('/signals/v1/private/users/{}'.format(
            self.sia_read_write_user.pk
        ), data=data, format='json')
        self.assertEqual(response.status_code, 200)

        self.sia_read_write_user.refresh_from_db()
        self.assertEqual(self.sia_read_write_user.profile.note, 'note #2')

        response_data = response.json()
        self.assertEqual(response_data['profile']['note'], 'note #2')

    @unittest.expectedFailure  # SIG-2210 PUT is no longer allowed so this test should fail
    def test_put_user(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.put('/signals/v1/private/users/{}'.format(
            self.sia_read_write_user.pk
        ), data={}, format='json')
        self.assertEqual(response.status_code, 200)

    def test_delete_users_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.delete('/signals/v1/private/users/{}'.format(
            self.sia_read_write_user.pk
        ))
        self.assertEqual(response.status_code, 403)

    def test_get_currently_logged_in_user(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get('/signals/v1/private/me/')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['id'], self.sia_read_write_user.pk)
        self.assertEqual(response_data['username'], self.sia_read_write_user.username)
        self.assertEqual(response_data['email'], self.sia_read_write_user.email)
        self.assertTrue(response_data['is_active'])
        self.assertFalse(response_data['is_staff'])
        self.assertFalse(response_data['is_superuser'])
        self.assertEqual(len(response_data['roles']), 1)
        self.assertEqual(len(response_data['permissions']), 5)

    def test_put_not_allowed(self):
        """
        SIG-2210 [BE] PUT op user detail accepteert leeg object

        At this moment we only implemented the partial update of a user. So we only accept the PATCH and no longer
        PUT when editing users.
        """
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.put('/signals/v1/private/users/{}'.format(
            self.sia_read_write_user.pk
        ), data={}, format='json')
        self.assertEqual(response.status_code, 405)

    def test_bug_post_username_already_exists(self):
        self.client.force_authenticate(user=self.superuser)

        data = {
            'username': self.superuser.username,
            'first_name': 'Test',
            'last_name': 'Tester',
            'is_active': True,
        }

        response = self.client.post('/signals/v1/private/users/', data=data, format='json')
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['username'][0], f'A user with username {self.superuser.username} already exists')

    def test_post_username_must_be_an_email(self):
        self.client.force_authenticate(user=self.superuser)

        data = {
            'username': 'username',
            'first_name': 'Test',
            'last_name': 'Tester',
            'is_active': True,
        }

        response = self.client.post('/signals/v1/private/users/', data=data, format='json')
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['username'][0], 'Voer een geldig e-mailadres in.')

    def test_get_unauthenticated(self):
        response = self.client.get('/signals/v1/private/me/')

        self.assertEqual(response.status_code, 401)

    def test_history_view(self):
        self.client.force_authenticate(user=self.superuser)

        group = Group.objects.create(name='Test group')

        url = f'/signals/v1/private/users/{self.superuser.pk}'

        response = self.client.patch(url, data={'first_name': 'Patched', 'role_ids': [group.pk]})
        self.assertEqual(response.status_code, 200)

        response = self.client.patch(url, data={'last_name': 'Patched', 'is_active': False})
        self.assertEqual(response.status_code, 200)

        history_url = f'{url}/history'
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

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
