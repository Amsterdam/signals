from unittest import skip
from unittest.mock import patch

from rest_framework.exceptions import AuthenticationFailed

from signals.auth.backend import JWTAuthBackend
from signals.auth.config import get_settings
from tests.test import SignalsBaseApiTestCase


class TestBackend(SignalsBaseApiTestCase):
    @skip('buggy test')
    @patch('signals.auth.tokens.JWTAccessToken.token_data')
    @patch('rest_framework.request')
    @patch('django.core.cache.cache')
    def test_user_not_in_cache(self, mock_cache, mock_request, mock_token_data):
        mock_request.is_authorized_for.return_value = True
        settings = get_settings()
        claims = {settings['USER_ID_FIELD']: self.superuser.username}
        mock_token_data.return_value = claims, self.superuser.username
        mock_cache.get.return_value = None

        user, scope = JWTAuthBackend.authenticate(mock_request)
        self.assertEqual(user.username, self.superuser.username)

    @skip("Scope test are not required")
    @patch('signals.auth.tokens.JWTAccessToken.token_data')
    @patch('rest_framework.request')
    @patch('django.core.cache.cache')
    def test_user_invalid_scope(self, mock_cache, mock_request, mock_token_data):
        mock_request.is_authorized_for.return_value = False
        settings = get_settings()
        claims = {settings['USER_ID_FIELD']: self.superuser.username}
        mock_token_data.return_value = claims, self.superuser.username
        mock_cache.get.return_value = None

        with self.assertRaises(AuthenticationFailed) as cm:
            JWTAuthBackend.authenticate(mock_request)

        e = cm.exception
        self.assertEqual(str(e), 'No token or required scope')

    @patch('signals.auth.tokens.JWTAccessToken.token_data')
    @patch('rest_framework.request')
    @patch('django.core.cache.cache')
    def test_user_does_not_exists(self, mock_cache, mock_request, mock_token_data):
        mock_request.is_authorized_for.return_value = True
        settings = get_settings()
        claims = {settings['USER_ID_FIELD']: 'idonotexist'}
        mock_token_data.return_value = claims, 'idonotexist'
        mock_cache.get.return_value = None

        with self.assertRaises(AuthenticationFailed) as cm:
            JWTAuthBackend.authenticate(mock_request)

        e = cm.exception
        self.assertEqual(str(e), 'User {} is not authorized'.format('idonotexist'))
