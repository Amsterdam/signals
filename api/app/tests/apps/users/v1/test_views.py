from tests.test import SIAReadUserMixin, SignalsBaseApiTestCase


class TestViews(SIAReadUserMixin, SignalsBaseApiTestCase):
    def test_get_users(self):
        self.client.force_authenticate(user=self.sia_read_user)
        response = self.client.get('/signals/v1/private/users/')
        self.assertEqual(response.status_code, 200)

    def test_get_roles(self):
        self.client.force_authenticate(user=self.sia_read_user)
        response = self.client.get('/signals/v1/private/roles/')
        self.assertEqual(response.status_code, 200)

    def test_get_permissions(self):
        self.client.force_authenticate(user=self.sia_read_user)
        response = self.client.get('/signals/v1/private/permissions/')
        self.assertEqual(response.status_code, 200)

    def test_get_users_not_authenticated(self):
        response = self.client.get('/signals/v1/private/users/')
        self.assertEqual(response.status_code, 401)

    def test_get_roles_not_authenticated(self):
        response = self.client.get('/signals/v1/private/roles/')
        self.assertEqual(response.status_code, 401)

    def test_get_permissions_not_authenticated(self):
        response = self.client.get('/signals/v1/private/permissions/')
        self.assertEqual(response.status_code, 401)
