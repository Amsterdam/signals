# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2025 Gemeente Amsterdam
from typing import override

from django.conf import settings
from django.contrib.auth.models import User
from mozilla_django_oidc.contrib.drf import OIDCAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request


class JWTAuthBackend(OIDCAuthentication):
    www_authenticate_realm = "signals"

    @override
    def authenticate(self, request: Request) -> tuple[User, str]:
        if settings.SIGNALS_AUTH.get("ALWAYS_OK", False):
            try:
                user = User.objects.get(username__iexact=settings.TEST_LOGIN)
            except User.DoesNotExist as e:
                raise AuthenticationFailed("User not found") from e

            return user, ""

        return super().authenticate(request)
