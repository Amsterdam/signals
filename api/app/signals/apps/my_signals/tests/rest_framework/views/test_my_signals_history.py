# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.test import override_settings
from django.urls import include, path
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_501_NOT_IMPLEMENTED
from rest_framework.test import APITestCase

from signals.apps.api.views import NamespaceView
from signals.apps.my_signals.models import Token
from signals.apps.signals.factories import SignalFactoryWithImage

urlpatterns = [
    path('v1/relations/', NamespaceView.as_view(), name='signal-namespace'),
    path('', include('signals.apps.my_signals.urls')),
]


class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns


@override_settings(ROOT_URLCONF=test_urlconf)
class TestMySignalsHistoryEndpoint(APITestCase):
    endpoint = '/my/signals'

    def setUp(self):
        self.signal = SignalFactoryWithImage.create(reporter__email='my-signals-test-reporter@example.com')
        token = Token.objects.create(reporter_email='my-signals-test-reporter@example.com')
        self.request_headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

    def test_my_signals_history_not_implemented(self):
        response = self.client.get(f'{self.endpoint}/{self.signal.uuid}/history', **self.request_headers)
        self.assertEqual(response.status_code, HTTP_501_NOT_IMPLEMENTED)


class TestMySignalsHistoryEndpointDisabled(APITestCase):
    endpoint = '/my/signals'

    def setUp(self):
        self.signal = SignalFactoryWithImage.create(reporter__email='my-signals-test-reporter@example.com')
        token = Token.objects.create(reporter_email='my-signals-test-reporter@example.com')
        self.request_headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

    def test_my_signals_history_feature_disabled(self):
        response = self.client.get(f'{self.endpoint}/{self.signal.uuid}/history', **self.request_headers)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        response = self.client.get(f'{self.endpoint}/{self.signal.uuid}/history')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
