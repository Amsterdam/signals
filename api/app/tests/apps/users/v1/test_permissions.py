from tests.test import SIAReadUserMixin, SignalsBaseApiTestCase


class TestPermissionsViews(SIAReadUserMixin, SignalsBaseApiTestCase):
    def test_get_permissions(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.get('/signals/v1/private/permissions/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['count'], 16)
        self.assertEqual(len(data['results']), 16)

    def test_get_permission(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.get('/signals/v1/private/permissions/{}'.format(
            self.sia_read.pk
        ))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['id'], self.sia_read.pk)
        self.assertEqual(data['name'], self.sia_read.name)
        self.assertEqual(data['codename'], self.sia_read.codename)

    def test_get_permissions_not_authenticated(self):
        response = self.client.get('/signals/v1/private/permissions/')
        self.assertEqual(response.status_code, 401)

    def test_post_permissions_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.post('/signals/v1/private/permissions/',
                                    data={})
        self.assertEqual(response.status_code, 403)

        response = self.client.post('/signals/v1/private/permissions/{}'.format(
            self.sia_read_user.pk
        ), data={})
        self.assertEqual(response.status_code, 403)

    def test_patch_permissions_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.patch('/signals/v1/private/permissions/',
                                     data={})
        self.assertEqual(response.status_code, 403)

        response = self.client.patch('/signals/v1/private/permissions/{}'.format(
            self.sia_read_user.pk
        ), data={})
        self.assertEqual(response.status_code, 403)

    def test_put_permissions_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.put('/signals/v1/private/permissions/',
                                   data={})
        self.assertEqual(response.status_code, 403)

        response = self.client.put('/signals/v1/private/permissions/{}'.format(
            self.sia_read_user.pk
        ), data={})
        self.assertEqual(response.status_code, 403)

    def test_delete_permissions_forbidden(self):
        self.client.force_authenticate(user=self.sia_read_user)

        response = self.client.delete('/signals/v1/private/permissions/')
        self.assertEqual(response.status_code, 403)

        response = self.client.delete('/signals/v1/private/permissions/{}'.format(
            self.sia_read_user.pk
        ))
        self.assertEqual(response.status_code, 403)
