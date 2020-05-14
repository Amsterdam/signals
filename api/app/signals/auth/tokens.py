from json import loads

from jwcrypto.jws import InvalidJWSSignature
from jwcrypto.jwt import JWT, JWTExpired, JWTMissingKey
from rest_framework.exceptions import AuthenticationFailed

from .config import get_settings
from .jwks import check_update_keyset, get_keyset


class JWTAccessToken():
    @staticmethod  # noqa: C901
    def decode_token(token=None, missing_key=False):
        settings = get_settings()
        try:
            jwt = JWT(jwt=token, key=get_keyset(), algs=settings['ALLOWED_SIGNING_ALGORITHMS'])
        except JWTExpired:
            raise AuthenticationFailed('API authz problem: token expired {}'.format(token))
        except InvalidJWSSignature as e:
            raise AuthenticationFailed('API authz problem: invalid signature. {}'.format(e))
        except ValueError as e:
            raise AuthenticationFailed('API authz problem: {}'.format(e))
        except JWTMissingKey:
            if missing_key:
                raise AuthenticationFailed('token key not present')
            check_update_keyset()
            return JWTAccessToken.decode_token(token=token, missing_key=True)
        return jwt

    @staticmethod  # noqa: C901
    def decode_claims(raw_claims):
        settings = get_settings()
        claims = loads(raw_claims)

        user_id = None
        try:
            user_id = claims[settings['USER_ID_FIELD']]
        except KeyError:
            raise AuthenticationFailed("Field '{}' missing".format(settings['USER_ID_FIELD']))

        return claims, user_id

    @staticmethod  # noqa: C901
    def token_data(authz_header, skip_always=False):
        settings = get_settings()
        if not skip_always and settings['ALWAYS_OK']:
            return {settings['USER_ID_FIELD']: "ALWAYS_OK"}, "ALWAYS_OK"
        try:
            prefix, raw_jwt = authz_header.split()
        except:  # noqa
            raise AuthenticationFailed('invalid token')

        if prefix.lower() != 'bearer':
            raise AuthenticationFailed('invalid token format')

        jwt = JWTAccessToken.decode_token(token=raw_jwt)
        return JWTAccessToken.decode_claims(jwt.claims)
