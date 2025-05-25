# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2025 Gemeente Amsterdam
from typing import override

from django.conf import settings
from django.contrib.auth.models import User
from jwcrypto.jwt import JWTMissingKey
from mozilla_django_oidc.contrib.drf import OIDCAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from .tokens import JWTAccessToken


class JWTAuthBackend(OIDCAuthentication):
    www_authenticate_realm = "signals"

    @override
    def authenticate(self, request: Request) -> tuple[User, str]:
        if settings.SIGNALS_AUTH.get("ALWAYS_OK", False):
            try:
                user = User.objects.get(username__iexact=settings.TEST_LOGIN, is_active=True)
            except User.DoesNotExist as e:
                raise AuthenticationFailed("User not found") from e

            return user, ""

        if settings.PUB_JWKS:
            try:
                auth_header = request.META.get('HTTP_AUTHORIZATION')

                _, user_id = JWTAccessToken.token_data(auth_header)
                try:
                    user = User.objects.get(username__iexact=user_id, is_active=True)
                except User.DoesNotExist as e:
                    raise AuthenticationFailed("User not found") from e

                return user, ""
            except JWTMissingKey:
                # Omit missing key, as it can also be another key that is used by amsterdam-django-oidc
                pass

        user, access_token = super().authenticate(request)

        if user is None:
            raise AuthenticationFailed("Incorrect access token provided")

        if not isinstance(user, User):
            raise AuthenticationFailed("Unknown error during authentication")

        if user.is_active is False:
            raise AuthenticationFailed("User is inactive")

        return user, access_token
