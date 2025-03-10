# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2024 Gemeente Amsterdam
from django.conf import settings
from django.contrib.auth.models import User
from mozilla_django_oidc.contrib.drf import OIDCAuthentication
from rest_framework.request import Request


class JWTAuthBackend(OIDCAuthentication):
    www_authenticate_realm = "signals"

    def authenticate(self, request: Request) -> tuple[User, str]:
        if settings.SIGNALS_AUTH.get("ALWAYS_OK", False):
            user = User.objects.get(username__iexact=settings.TEST_LOGIN)
            return user, ""

        return super().authenticate(request)
