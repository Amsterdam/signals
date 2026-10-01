# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from signals.middleware import ContentSecurityPolicyMiddleware


class TestContentSecurityPolicyMiddleware(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def get_response(self, path, content_type='text/html'):
        middleware = ContentSecurityPolicyMiddleware(
            lambda request: HttpResponse(content_type=content_type)
        )
        return middleware(self.request_factory.get(path))

    def test_adds_content_security_policy_to_admin_response(self):
        response = self.get_response('/signals/admin/login/')

        policy = response['Content-Security-Policy']
        for directive in (
            "default-src 'self'",
            "connect-src 'self' https://cdn.jsdelivr.net",
            "frame-ancestors 'none'",
            "img-src 'self' data: https://tile.openstreetmap.org",
            "object-src 'none'",
            "script-src 'self' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        ):
            with self.subTest(directive=directive):
                self.assertIn(directive, policy)

        script_policy = next(item for item in policy.split('; ') if item.startswith('script-src'))
        self.assertNotIn("'unsafe-inline'", script_policy)

    def test_adds_content_security_policy_to_browsable_api_response(self):
        response = self.get_response('/signals/v1/public/terms/categories/')

        policy = response['Content-Security-Policy']
        self.assertIn("script-src 'self'", policy)
        self.assertNotIn('https://cdn.jsdelivr.net', policy)

    def test_allows_swagger_inline_initialization(self):
        response = self.get_response('/signals/swagger/')

        policy = response['Content-Security-Policy']
        self.assertIn("script-src 'self' 'unsafe-inline'", policy)

    def test_does_not_add_content_security_policy_to_json_response(self):
        response = self.get_response('/signals/status/', content_type='application/json')

        self.assertNotIn('Content-Security-Policy', response)

    def test_preserves_existing_content_security_policy(self):
        def get_response(request):
            return HttpResponse(
                headers={'Content-Security-Policy': "default-src 'none'"},
            )

        middleware = ContentSecurityPolicyMiddleware(get_response)
        response = middleware(self.request_factory.get('/signals/admin/login/'))

        self.assertEqual(response['Content-Security-Policy'], "default-src 'none'")
