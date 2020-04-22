from json import loads

from jwcrypto.jws import InvalidJWSSignature
from jwcrypto.jwt import JWT, JWTExpired, JWTMissingKey

from .config import get_settings
from .errors import AuthorizationHeaderError, AuthzConfigurationError, invalid_request
from .jwks import get_keyset


class JWTAccessToken():
    @staticmethod  # noqa: C901
    def decode_token(token=None):
        settings = get_settings()
        try:
            jwt = JWT(jwt=token, key=get_keyset(), algs=settings['ALLOWED_SIGNING_ALGORITHMS'])
        except JWTExpired:
            raise AuthzConfigurationError('API authz problem: token expired {}'.format(token))
        except InvalidJWSSignature as e:
            raise AuthzConfigurationError('API authz problem: invalid signature. {}'.format(e))
        except ValueError as e:
            raise AuthzConfigurationError('API authz problem: {}'.format(e))

        return jwt

    @staticmethod  # noqa: C901
    def token_data(authz_header):
        settings = get_settings()
        if settings['ALWAYS_OK']:
            return {settings['USER_ID_FIELD']: "ALWAYS_OK"}, "ALWAYS_OK"
        try:
            prefix, raw_jwt = authz_header.split()
        except ValueError:
            raise AuthorizationHeaderError(invalid_request())

        if prefix.lower() != 'bearer':
            raise AuthorizationHeaderError(invalid_request())

        try:
            jwt = JWTAccessToken.decode_token(raw_jwt)
        except JWTMissingKey:
            raise AuthorizationHeaderError(invalid_request())
        claims = loads(jwt.claims)
        # token_signature = raw_jwt.split('.')[2]
        return claims, claims[settings['USER_ID_FIELD']]
