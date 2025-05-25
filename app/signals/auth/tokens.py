# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from json import loads

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from jwcrypto.jws import InvalidJWSObject, InvalidJWSSignature
from jwcrypto.jwt import JWT, JWTExpired
from rest_framework.exceptions import AuthenticationFailed

from .jwks import get_keyset

ALLOWED_SIGNING_ALGS = [
    'HS256', 'HS384', 'HS512',
    'ES256', 'ES384', 'ES512',
    'RS256', 'RS384', 'RS512'
]


class JWTAccessToken:
    @staticmethod  # noqa: C901
    def decode_token(token=None):
        try:
            jwt = JWT(jwt=token, key=get_keyset(), algs=ALLOWED_SIGNING_ALGS)
        except JWTExpired:
            raise AuthenticationFailed(f'API auth problem: token expired {token}')
        except InvalidJWSSignature:
            raise AuthenticationFailed('API auth problem: invalid signature.')
        except ValueError:
            raise AuthenticationFailed('API auth problem: value error')
        except InvalidJWSObject:
            raise AuthenticationFailed('Invalid JWS Object')
        return jwt

    @staticmethod  # noqa: C901
    def decode_claims(raw_claims):
        claims = loads(raw_claims)

        user_id = claims.get('email', None)
        if user_id:
            try:
                validate_email(user_id)  # Signalen uses email addresses as usernames
            except ValidationError:
                user_id = None
        else:
            raise AuthenticationFailed('Could not validate user with email')

        return claims, user_id  # only user_id is used, SIA contains its own authorization model

    @staticmethod  # noqa: C901
    def token_data(auth_header, skip_always=False):
        try:
            prefix, raw_jwt = auth_header.split()
        except:  # noqa
            raise AuthenticationFailed('invalid token')

        if prefix.lower() != 'bearer':
            raise AuthenticationFailed('invalid token format')

        jwt = JWTAccessToken.decode_token(token=raw_jwt)
        return JWTAccessToken.decode_claims(jwt.claims)
