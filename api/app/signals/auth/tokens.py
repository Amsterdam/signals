# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from json import loads

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from jwcrypto.jws import InvalidJWSObject, InvalidJWSSignature
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
        except InvalidJWSObject as e:
            raise AuthenticationFailed(f'{e}')
        return jwt

    @staticmethod  # noqa: C901
    def decode_claims(raw_claims):
        settings = get_settings()
        claims = loads(raw_claims)

        # To temporarily support both authz tokens and KeyCloak tokens, we have
        # to check the "sub" (authz) and "email" (KeyCloak and Dex) fields.
        # Here we loop through the configured user id fields and check whether
        # they are present and if so, if they contain an email address.
        for user_id_field in settings['USER_ID_FIELDS']:
            user_id = claims.get(user_id_field, None)
            if user_id:
                try:
                    validate_email(user_id)  # SIA / Signalen uses email addresses as usernames
                except ValidationError:
                    user_id = None
                else:
                    break  # we identified the correct user_id_field and user email
        else:
            msg = 'Fields {} are missing or do not contain user email.'
            raise AuthenticationFailed(msg.format(','.join(settings['USER_ID_FIELDS'])))

        return claims, user_id  # only user_id is used, SIA contains its own authorization model

    @staticmethod  # noqa: C901
    def token_data(authz_header, skip_always=False):
        settings = get_settings()
        if not skip_always and settings['ALWAYS_OK']:
            return {x: "ALWAYS_OK" for x in settings['USER_ID_FIELDS']}, "ALWAYS_OK"
        try:
            prefix, raw_jwt = authz_header.split()
        except:  # noqa
            raise AuthenticationFailed('invalid token')

        if prefix.lower() != 'bearer':
            raise AuthenticationFailed('invalid token format')

        jwt = JWTAccessToken.decode_token(token=raw_jwt)
        return JWTAccessToken.decode_claims(jwt.claims)
