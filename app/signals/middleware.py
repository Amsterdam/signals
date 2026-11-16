# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from typing import Callable

from django.http import HttpRequest, HttpResponse

CONTENT_SECURITY_POLICY = '; '.join([
    "default-src 'self'",
    "base-uri 'self'",
    "connect-src 'self'",
    "font-src 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "img-src 'self' data:",
    "object-src 'none'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
])

ADMIN_CONTENT_SECURITY_POLICY = '; '.join([
    "default-src 'self'",
    "base-uri 'self'",
    "connect-src 'self' https://cdn.jsdelivr.net",
    "font-src 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "img-src 'self' data: https://tile.openstreetmap.org",
    "object-src 'none'",
    "script-src 'self' https://cdn.jsdelivr.net",
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
])

SWAGGER_CONTENT_SECURITY_POLICY = '; '.join([
    "default-src 'self'",
    "base-uri 'self'",
    "connect-src 'self'",
    "font-src 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "img-src 'self' data:",
    "object-src 'none'",
    "script-src 'self' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline'",
])


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        content_type = response.get('Content-Type', '').partition(';')[0].lower()
        if content_type != 'text/html':
            return response

        if request.path.startswith('/signals/admin/'):
            policy = ADMIN_CONTENT_SECURITY_POLICY
        elif request.path.startswith('/signals/swagger/'):
            policy = SWAGGER_CONTENT_SECURITY_POLICY
        else:
            policy = CONTENT_SECURITY_POLICY

        response.setdefault('Content-Security-Policy', policy)

        return response
