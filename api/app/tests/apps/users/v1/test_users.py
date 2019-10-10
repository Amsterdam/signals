from tests.test import SIAReadUserMixin, SignalsBaseApiTestCase


class TestUsersViews(SIAReadUserMixin, SignalsBaseApiTestCase):
    def test_get_users(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.get('/signals/v1/private/users/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['results']), 1)

        data_user = data['results'][0]
        self.assertEqual(data_user['id'], self.sia_read_user.pk)
        self.assertEqual(data_user['username'], self.sia_read_user.username)
        self.assertTrue(data_user['is_active'])
        self.assertEqual(len(data_user['roles']), 0)

    def test_get_user(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.get('/signals/v1/private/users/{}'.format(self.sia_read_user.pk))
        self.assertEqual(response.status_code, 200)

        data_user = response.json()
        self.assertEqual(data_user['id'], self.sia_read_user.pk)
        self.assertEqual(data_user['username'], self.sia_read_user.username)
        self.assertEqual(data_user['email'], self.sia_read_user.email)
        self.assertTrue(data_user['is_active'])
        self.assertFalse(data_user['is_staff'])
        self.assertFalse(data_user['is_superuser'])
        self.assertEqual(len(data_user['roles']), 0)
        self.assertEqual(len(data_user['permissions']), 1)

        self.assertEqual(data_user['permissions'][0]['id'], self.sia_read.pk)
        self.assertEqual(data_user['permissions'][0]['name'], self.sia_read.name)
        self.assertEqual(data_user['permissions'][0]['codename'], self.sia_read.codename)

    def test_get_users_not_authenticated(self):
        response = self.client.get('/signals/v1/private/users/')
        self.assertEqual(response.status_code, 401)

    def test_post_users_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.post('/signals/v1/private/users/',
                                    data={})
        self.assertEqual(response.status_code, 403)

        response = self.client.post('/signals/v1/private/users/{}'.format(self.sia_read_user.pk),
                                    data={})
        self.assertEqual(response.status_code, 403)

    def test_patch_users_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.patch('/signals/v1/private/users/',
                                     data={})
        self.assertEqual(response.status_code, 403)

        response = self.client.patch('/signals/v1/private/users/{}'.format(self.sia_read_user.pk),
                                     data={})
        self.assertEqual(response.status_code, 403)

    def test_put_users_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.put('/signals/v1/private/users/',
                                   data={})
        self.assertEqual(response.status_code, 403)

        response = self.client.put('/signals/v1/private/users/{}'.format(self.sia_read_user.pk),
                                   data={})
        self.assertEqual(response.status_code, 403)

    def test_delete_users_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.delete('/signals/v1/private/users/')
        self.assertEqual(response.status_code, 403)

        response = self.client.delete('/signals/v1/private/users/{}'.format(self.sia_read_user.pk))
        self.assertEqual(response.status_code, 403)
