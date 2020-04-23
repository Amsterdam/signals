from json import loads

from jwcrypto.jws import InvalidJWSSignature
from jwcrypto.jwt import JWT, JWTExpired, JWTMissingKey
from rest_framework.exceptions import AuthenticationFailed

from .config import get_settings
from .jwks import get_keyset


class JWTAccessToken():
    @staticmethod  # noqa: C901
    def decode_token(token=None):
        settings = get_settings()
        try:
            jwt = JWT(jwt=token, key=get_keyset(), algs=settings['ALLOWED_SIGNING_ALGORITHMS'])
        except JWTExpired:
            raise AuthenticationFailed('API authz problem: token expired {}'.format(token))
        except InvalidJWSSignature as e:
            raise AuthenticationFailed('API authz problem: invalid signature. {}'.format(e))
        except ValueError as e:
            raise AuthenticationFailed('API authz problem: {}'.format(e))

        return jwt

    @staticmethod  # noqa: C901
    def token_data(authz_header, skip_always=False):
        settings = get_settings()
        if not skip_always and settings['ALWAYS_OK']:
            return {settings['USER_ID_FIELD']: "ALWAYS_OK"}, "ALWAYS_OK"
        try:
            prefix, raw_jwt = authz_header.split()
        except ValueError:
            raise AuthenticationFailed('invalid token')

        if prefix.lower() != 'bearer':
            raise AuthenticationFailed('invalid token format')

        try:
            jwt = JWTAccessToken.decode_token(raw_jwt)
        except JWTMissingKey:
            raise AuthenticationFailed('token key not present')
        claims = loads(jwt.claims)
        # token_signature = raw_jwt.split('.')[2]
        return claims, claims[settings['USER_ID_FIELD']]
