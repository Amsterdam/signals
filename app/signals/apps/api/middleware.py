# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam
from typing import Callable

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse

from signals import VERSION
from signals.utils.version import get_version


class APIVersionHeaderMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Versioning
        # ==========
        # SIA / Signalen follows the semantic versioning standard. Previously we had
        # separate version numbers for the V0 (now defunct) and V1 versions of the API.
        # We now no longer separately version these, as their releases were always
        # tied to the backend. For backwards compatibility, and to not break external
        # systems that rely on SIA / Signalen we still expose all the separate version
        # numbers, but they are now all the same.

        response = self.get_response(request)
        response['X-API-Version'] = get_version(VERSION)
        return response


class SessionLoginMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if request.user and not isinstance(request.user, AnonymousUser):
            if request.path.startswith('/signals/v1/private'):
                login(request, request.user, settings.AUTHENTICATION_BACKENDS[0])

        return response
