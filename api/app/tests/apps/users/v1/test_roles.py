from django.contrib.auth.models import Permission

from tests.apps.users.factories import GroupFactory
from tests.test import SIAReadWriteUserMixin, SignalsBaseApiTestCase


class TestRolesViews(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        permission = Permission.objects.get(codename='add_group')
        self.sia_read_write_user.user_permissions.add(permission)

        permission = Permission.objects.get(codename='change_group')
        self.sia_read_write_user.user_permissions.add(permission)

        self.group_no_permissions = GroupFactory.create(name='A group with no permissions')

        self.group_with_permissions = GroupFactory.create(name='This group does have permissions')
        self.group_with_permissions.permissions.add(self.sia_read)

    def test_get_roles(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get('/signals/v1/private/roles/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['results']), 3)

        self.assertEqual(data['results'][0]['id'], self.group_no_permissions.pk)
        self.assertEqual(data['results'][0]['name'], self.group_no_permissions.name)
        self.assertEqual(len(data['results'][0]['permissions']), 0)

        self.assertEqual(data['results'][1]['id'], self.sia_test_group.pk)
        self.assertEqual(data['results'][1]['name'], self.sia_test_group.name)

        self.assertEqual(data['results'][2]['id'], self.group_with_permissions.pk)
        self.assertEqual(data['results'][2]['name'], self.group_with_permissions.name)
        self.assertEqual(len(data['results'][2]['permissions']), 1)
        self.assertEqual(data['results'][2]['permissions'][0]['id'], self.sia_read.pk)
        self.assertEqual(data['results'][2]['permissions'][0]['name'], self.sia_read.name)
        self.assertEqual(data['results'][2]['permissions'][0]['codename'], self.sia_read.codename)

    def test_get_role_no_permissions(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get('/signals/v1/private/roles/{}'.format(
            self.group_no_permissions.pk
        ))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['id'], self.group_no_permissions.pk)
        self.assertEqual(data['name'], self.group_no_permissions.name)
        self.assertEqual(len(data['permissions']), 0)

    def test_get_role_with_permissions(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.get('/signals/v1/private/roles/{}'.format(
            self.group_with_permissions.pk
        ))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['id'], self.group_with_permissions.pk)
        self.assertEqual(data['name'], self.group_with_permissions.name)
        self.assertEqual(len(data['permissions']), 1)
        self.assertEqual(data['permissions'][0]['id'], self.sia_read.pk)
        self.assertEqual(data['permissions'][0]['name'], self.sia_read.name)
        self.assertEqual(data['permissions'][0]['codename'], self.sia_read.codename)

    def test_get_roles_not_authenticated(self):
        response = self.client.get('/signals/v1/private/roles/')
        self.assertEqual(response.status_code, 401)

    def test_post_role_no_permissions(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'name': 'sia_test_group_1',
        }

        response = self.client.post('/signals/v1/private/roles/', data=data)
        self.assertEqual(response.status_code, 201)

        response_data = response.json()
        self.assertIsNotNone(response_data['id'])
        self.assertEqual(response_data['name'], data['name'])
        self.assertEqual(len(response_data['permissions']), 0)

    def test_post_role_with_permissions(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'name': 'sia_test_group_1',
            'permission_ids': [self.sia_read.pk, self.sia_write.pk]
        }

        response = self.client.post('/signals/v1/private/roles/', data=data)
        self.assertEqual(response.status_code, 201)

        response_data = response.json()
        self.assertIsNotNone(response_data['id'])
        self.assertEqual(response_data['name'], data['name'])
        self.assertEqual(len(response_data['permissions']), 2)

        for p in response_data['permissions']:
            self.assertIn(p['id'], [self.sia_read.pk, self.sia_write.pk])
            self.assertIn(p['name'], [self.sia_read.name, self.sia_write.name])
            self.assertIn(p['codename'], [self.sia_read.codename, self.sia_write.codename])

    def test_patch_role(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'name': 'sia_changed_group_with_permissions'
        }

        self.assertNotEqual(self.group_with_permissions.name, data['name'])

        response = self.client.patch('/signals/v1/private/roles/{}'.format(
            self.group_with_permissions.pk
        ), data=data)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['id'], self.group_with_permissions.pk)
        self.assertEqual(response_data['name'], data['name'])
        self.assertEqual(len(response_data['permissions']),
                         self.group_with_permissions.permissions.count())

        self.group_with_permissions.refresh_from_db()
        self.assertEqual(self.group_with_permissions.name, data['name'])

    def test_patch_role_permissions(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'permission_ids': [self.sia_write.pk, self.sia_read.pk]
        }

        self.assertEqual(self.group_with_permissions.permissions.count(), 1)

        response = self.client.patch('/signals/v1/private/roles/{}'.format(
            self.group_with_permissions.pk
        ), data=data)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['id'], self.group_with_permissions.pk)
        self.assertEqual(response_data['name'], self.group_with_permissions.name)
        self.assertEqual(len(response_data['permissions']), 2)

        for p in response_data['permissions']:
            self.assertIn(p['id'], [self.sia_read.pk, self.sia_write.pk])
            self.assertIn(p['name'], [self.sia_read.name, self.sia_write.name])
            self.assertIn(p['codename'], [self.sia_read.codename, self.sia_write.codename])

        self.group_with_permissions.refresh_from_db()
        self.assertEqual(self.group_with_permissions.permissions.count(), 2)

    def test_put_role(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        data = {
            'name': 'sia_changed_group_with_permissions'
        }

        self.assertNotEqual(self.group_with_permissions.name, data['name'])

        response = self.client.patch('/signals/v1/private/roles/{}'.format(
            self.group_with_permissions.pk
        ), data=data)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['id'], self.group_with_permissions.pk)
        self.assertEqual(response_data['name'], data['name'])
        self.assertEqual(len(response_data['permissions']),
                         self.group_with_permissions.permissions.count())

        self.group_with_permissions.refresh_from_db()
        self.assertEqual(self.group_with_permissions.name, data['name'])

    def test_delete_roles_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_write_user)

        response = self.client.delete('/signals/v1/private/roles/')
        self.assertEqual(response.status_code, 403)

        response = self.client.delete('/signals/v1/private/roles/{}'.format(
            self.group_with_permissions.pk
        ))
        self.assertEqual(response.status_code, 403)
