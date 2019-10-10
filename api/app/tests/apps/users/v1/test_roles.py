from tests.apps.users.factories import GroupFactory
from tests.test import SIAReadUserMixin, SignalsBaseApiTestCase


class TestRolesViews(SIAReadUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        self.group_no_permissions = GroupFactory.create()

        self.group_with_permissions = GroupFactory.create()
        self.group_with_permissions.permissions.add(self.sia_read)

    def test_get_roles(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.get('/signals/v1/private/roles/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['results']), 2)

        self.assertEqual(data['results'][0]['id'], self.group_no_permissions.pk)
        self.assertEqual(data['results'][0]['name'], self.group_no_permissions.name)
        self.assertEqual(len(data['results'][0]['permissions']), 0)

        self.assertEqual(data['results'][1]['id'], self.group_with_permissions.pk)
        self.assertEqual(data['results'][1]['name'], self.group_with_permissions.name)
        self.assertEqual(len(data['results'][1]['permissions']), 1)
        self.assertEqual(data['results'][1]['permissions'][0]['id'], self.sia_read.pk)
        self.assertEqual(data['results'][1]['permissions'][0]['name'], self.sia_read.name)
        self.assertEqual(data['results'][1]['permissions'][0]['codename'], self.sia_read.codename)

    def test_get_role_no_permissions(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.get('/signals/v1/private/roles/{}'.format(
            self.group_no_permissions.pk
        ))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['id'], self.group_no_permissions.pk)
        self.assertEqual(data['name'], self.group_no_permissions.name)
        self.assertEqual(len(data['permissions']), 0)

    def test_get_role_with_permissions(self):
        self.client.force_authenticate(user=self.sia_read_user)

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

    def test_post_roles_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.post('/signals/v1/private/roles/',
                                    data={})
        self.assertEqual(response.status_code, 403)

        response = self.client.post('/signals/v1/private/roles/{}'.format(self.sia_read_user.pk),
                                    data={})
        self.assertEqual(response.status_code, 403)

    def test_patch_roles_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.patch('/signals/v1/private/roles/',
                                     data={})
        self.assertEqual(response.status_code, 403)

        response = self.client.patch('/signals/v1/private/roles/{}'.format(self.sia_read_user.pk),
                                     data={})
        self.assertEqual(response.status_code, 403)

    def test_put_roles_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.put('/signals/v1/private/roles/',
                                   data={})
        self.assertEqual(response.status_code, 403)

        response = self.client.put('/signals/v1/private/roles/{}'.format(self.sia_read_user.pk),
                                   data={})
        self.assertEqual(response.status_code, 403)

    def test_delete_roles_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.delete('/signals/v1/private/roles/')
        self.assertEqual(response.status_code, 403)

        response = self.client.delete('/signals/v1/private/roles/{}'.format(self.sia_read_user.pk))
        self.assertEqual(response.status_code, 403)
