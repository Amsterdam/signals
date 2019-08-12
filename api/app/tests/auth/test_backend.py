from unittest.mock import patch

from rest_framework.exceptions import AuthenticationFailed

from signals.auth.backend import JWTAuthBackend
from tests.test import SignalsBaseApiTestCase


class TestBackend(SignalsBaseApiTestCase):
    @patch('django.core.cache.cache')
    @patch('rest_framework.request')
    def test_user_not_in_cache(self, mock_cache, mock_request):
        mock_request.is_authorized_for.return_value = True
        mock_request.get_token_subject.lower.return_value = self.superuser.username
        mock_cache.get.return_value = None

        user, scope = JWTAuthBackend.authenticate(mock_request)

        self.assertEqual(user.username, self.superuser.username)

    @patch('django.core.cache.cache')
    @patch('rest_framework.request')
    def test_user_invalid_scope(self, mock_cache, mock_request):
        mock_request.is_authorized_for.return_value = False
        mock_request.get_token_subject.lower.return_value = self.superuser.username
        mock_cache.get.return_value = None

        with self.assertRaises(AuthenticationFailed) as cm:
            JWTAuthBackend.authenticate(mock_request)

        e = cm.exception
        self.assertEqual(str(e), 'No token or required scope')

    @patch('django.core.cache.cache')
    @patch('rest_framework.request')
    def test_user_does_not_exists(self, mock_cache, mock_request):
        mock_request.is_authorized_for.return_value = True
        mock_request.get_token_subject.lower.return_value = 'idonotexist'
        mock_cache.get.return_value = None

        with self.assertRaises(AuthenticationFailed) as cm:
            JWTAuthBackend.authenticate(mock_request)

        e = cm.exception
        self.assertEqual(str(e), 'User {} is not authorized'.format('idonotexist'))
