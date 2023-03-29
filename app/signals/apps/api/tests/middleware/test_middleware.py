# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.test import modify_settings

from signals.test.utils import SIAReadUserMixin, SignalsBaseApiTestCase


@modify_settings(MIDDLEWARE={'append': 'signals.apps.api.middleware.SessionLoginMiddleware'})
class TestSessionLoginMiddleware(SIAReadUserMixin, SignalsBaseApiTestCase):
    def setUp(self):
        self.client.force_authenticate(user=self.sia_read_user)

    def test_session_cookie_is_provided_on_private_endpoint(self):
        response = self.client.get('/signals/v1/private/signals/')
        self.assertIsNotNone(response.cookies.get('sessionid'))

    def test_session_cookie_is_not_provided_on_public_endpoint(self):
        response = self.client.get('/signals/v1/public/terms/categories/')
        self.assertIsNone(response.cookies.get('sessionid'))
