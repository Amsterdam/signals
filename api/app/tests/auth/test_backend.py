import time
from unittest import skip
from unittest.mock import patch

from jwcrypto import jwt
from rest_framework.exceptions import AuthenticationFailed

from signals.auth.backend import JWTAuthBackend
from signals.auth.config import get_settings
from signals.auth.jwks import get_keyset
from signals.auth.tokens import JWTAccessToken
from tests.test import SignalsBaseApiTestCase


class TestBackend(SignalsBaseApiTestCase):
    def test_auth_verify_bearer_token(self):
        settings = get_settings()
        keyset = get_keyset()
        kid = "2aedafba-8170-4064-b704-ce92b7c89cc6"
        key = keyset.get_key(kid)

        token = jwt.JWT(header={"kid": kid, "alg": "ES256"},
                        claims={settings['USER_ID_FIELD']: "test@example.com"})
        token.make_signed_token(key)
        bearer = token.serialize()

        decoded_claims, user_id = JWTAccessToken.token_data('Bearer {}'.format(bearer), True)
        self.assertEqual(user_id, "test@example.com")

    def test_auth_verify_broken_bearer_token(self):
        with self.assertRaises(AuthenticationFailed):
            decoded_claims, user_id = JWTAccessToken.token_data('incorrect_format', True)

        with self.assertRaises(AuthenticationFailed):
            decoded_claims, user_id = JWTAccessToken.token_data('token xyz', True)

    def test_auth_verify_bearer_token_missing_user_id(self):
        keyset = get_keyset()
        kid = "2aedafba-8170-4064-b704-ce92b7c89cc6"
        key = keyset.get_key(kid)

        token = jwt.JWT(header={"kid": kid, "alg": "ES256"},
                        claims={'will_not_match': "test@example.com"})
        token.make_signed_token(key)
        bearer = 'Bearer {}'.format(token.serialize())

        with self.assertRaises(AuthenticationFailed):
            decoded_claims, user_id = JWTAccessToken.token_data(bearer, True)

    def test_auth_verify_bearer_token_invalid_signature(self):
        keyset = get_keyset()
        kid = "2aedafba-8170-4064-b704-ce92b7c89cc6"
        key = keyset.get_key(kid)

        token = jwt.JWT(header={"kid": kid, "alg": "ES256"},
                        claims={'will_not_match': "test@example.com"})
        token.make_signed_token(key)
        bearer = 'Bearer {}make_sig_invalid'.format(token.serialize())

        with self.assertRaises(AuthenticationFailed) as cm:
            decoded_claims, user_id = JWTAccessToken.token_data(bearer, True)
        e = cm.exception
        self.assertTrue(str(e).startswith('API authz problem: invalid signature'))

    def test_auth_verify_bearer_token_missing_signature(self):
        keyset = get_keyset()
        kid = "2aedafba-8170-4064-b704-ce92b7c89cc6"
        key = keyset.get_key(kid)

        token = jwt.JWT(header={"kid": "wrong_key_id", "alg": "ES256"},
                        claims={'will_not_match': "test@example.com"})
        token.make_signed_token(key)
        bearer = 'Bearer {}'.format(token.serialize())

        with self.assertRaises(AuthenticationFailed) as cm:
            decoded_claims, user_id = JWTAccessToken.token_data(bearer, True)
        e = cm.exception
        self.assertTrue(str(e).startswith('token key not present'))

    def test_auth_verify_bearer_expired_token(self):
        settings = get_settings()
        keyset = get_keyset()
        kid = "2aedafba-8170-4064-b704-ce92b7c89cc6"
        key = keyset.get_key(kid)
        exp_time = round(time.time()) - 1000
        token = jwt.JWT(header={"kid": kid, "alg": "ES256"},
                        claims={'exp': exp_time, settings['USER_ID_FIELD']: 'test@test.com'})
        token.make_signed_token(key)
        bearer = 'Bearer {}'.format(token.serialize())

        with self.assertRaises(AuthenticationFailed) as cm:
            decoded_claims, user_id = JWTAccessToken.token_data(bearer, True)
        e = cm.exception
        self.assertTrue(str(e).startswith('API authz problem: token expired'))

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
