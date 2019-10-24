from django.contrib.auth.models import Permission

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
        self.assertEqual(len(response_data['roles']), 0)

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
        self.assertEqual(len(response_data['roles']), 0)
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
            'permission_ids': [self.sia_read.pk, ],
        }

        response = self.client.post('/signals/v1/private/users/', data=data)
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

        self.assertEqual(len(response_data['permissions']), 1)
        self.assertEqual(response_data['permissions'][0]['id'], self.sia_read.pk)
        self.assertEqual(response_data['permissions'][0]['name'], self.sia_read.name)
        self.assertEqual(response_data['permissions'][0]['codename'], self.sia_read.codename)

    def test_post_users_invalid_data(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'username': 'this is not an email address',
            'is_active': 'not a boolean',
            'role_ids': [666666, ],  # non existing role
            'permission_ids': [666666, ],  # non existing permission
        }

        response = self.client.post('/signals/v1/private/users/', data=data)
        self.assertEqual(response.status_code, 400)

        response_data = response.json()
        self.assertEqual(len(response_data), 4)
        self.assertIsNotNone('username', response_data)
        self.assertIsNotNone('is_active', response_data)
        self.assertIsNotNone('role_ids', response_data)
        self.assertIsNotNone('permission_ids', response_data)

        self.assertEqual(response_data['username'][0], 'Voer een geldig e-mailadres in.')
        self.assertEqual(response_data['is_active'][0], 'Must be a valid boolean.')
        self.assertEqual(response_data['role_ids'][0], 'Ongeldige pk "666666" - object bestaat niet.')  # noqa
        self.assertEqual(response_data['permission_ids'][0], 'Ongeldige pk "666666" - object bestaat niet.')  # noqa

    def test_patch_user(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'username': 'this.is.the.new.address@test.com',
            'is_active': False,
        }

        response = self.client.patch('/signals/v1/private/users/{}'.format(
            self.sia_read_write_user.pk
        ), data=data)
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

    def test_put_user(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.put('/signals/v1/private/users/{}'.format(
            self.sia_read_write_user.pk
        ), data={})
        self.assertEqual(response.status_code, 200)

    def test_delete_users_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.delete('/signals/v1/private/users/{}'.format(
            self.sia_read_write_user.pk
        ))
        self.assertEqual(response.status_code, 403)
