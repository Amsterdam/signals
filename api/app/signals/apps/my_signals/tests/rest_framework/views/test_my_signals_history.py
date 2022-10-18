# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import copy

from django.conf import settings
from django.test import override_settings
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_501_NOT_IMPLEMENTED
from rest_framework.test import APITestCase

from signals.apps.my_signals.models import Token
from signals.apps.signals.factories import SignalFactoryWithImage


class TestMySignalsHistoryEndpoint(APITestCase):
    endpoint = '/signals/v1/my/signals'

    def setUp(self):
        self.feature_flags_enabled = settings.FEATURE_FLAGS
        self.feature_flags_enabled['MY_SIGNALS_ENABLED'] = True

        self.feature_flags_disabled = copy.deepcopy(self.feature_flags_enabled)
        self.feature_flags_disabled['MY_SIGNALS_ENABLED'] = False

        self.signal = SignalFactoryWithImage.create(reporter__email='my-signals-test-reporter@example.com')

        token = Token.objects.create(reporter_email='my-signals-test-reporter@example.com')
        self.request_headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

    def test_my_signals_history_not_implemented(self):
        with override_settings(FEATURE_FLAGS=self.feature_flags_enabled):
            response = self.client.get(f'{self.endpoint}/{self.signal.uuid}/history', **self.request_headers)
            self.assertEqual(response.status_code, HTTP_501_NOT_IMPLEMENTED)

    def test_my_signals_history_feature_disabled(self):
        with override_settings(FEATURE_FLAGS=self.feature_flags_disabled):
            response = self.client.get(f'{self.endpoint}/{self.signal.uuid}/history', **self.request_headers)
            self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
