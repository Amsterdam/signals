# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.db.models import Q
from django.test import override_settings
from django.urls import include, path
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase

from signals.apps.api.views import NamespaceView
from signals.apps.my_signals.models import Token
from signals.apps.signals.factories import SignalFactoryWithImage
from signals.apps.signals.models import Signal
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD, GESPLITST

urlpatterns = [
    path('v1/relations/', NamespaceView.as_view(), name='signal-namespace'),
    path('', include('signals.apps.my_signals.urls')),
]


class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns


@override_settings(ROOT_URLCONF=test_urlconf)
class TestMySignalsListEndpoint(APITestCase):
    endpoint = '/my/signals/'

    def setUp(self):
        signals_with_image_open_state = SignalFactoryWithImage.create_batch(
            5, reporter__email='my-signals-test-reporter@example.com'
        )
        signals_with_image_closed_state = SignalFactoryWithImage.create_batch(
            5, status__state=AFGEHANDELD, reporter__email='my-signals-test-reporter@example.com'
        )

        # Create a couple of children that should not be retrieved in the list
        SignalFactoryWithImage.create_batch(
            2, parent=signals_with_image_open_state[0], reporter__email='my-signals-test-reporter@example.com'
        )
        SignalFactoryWithImage.create_batch(
            2, parent=signals_with_image_closed_state[0], reporter__email='my-signals-test-reporter@example.com'
        )

        token = Token.objects.create(reporter_email='my-signals-test-reporter@example.com')
        self.request_headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

    def test_my_signals(self):
        # We should have 14 signals in the database
        # 2 parent signals
        self.assertEqual(2, Signal.objects.filter(children__isnull=False).distinct().count())
        # 4 child signals
        self.assertEqual(4, Signal.objects.filter(parent__isnull=False).count())
        # 8 "normal: signals
        self.assertEqual(8, Signal.objects.exclude(Q(children__isnull=False) | Q(parent__isnull=False)).count())

        response = self.client.get(self.endpoint, **self.request_headers)
        self.assertEqual(response.status_code, HTTP_200_OK)

        signals_qs = Signal.objects.exclude(parent__isnull=False).order_by('-created_at')

        data = response.json()
        self.assertEqual(len(data['results']), signals_qs.count())

        for signal, signal_response_data in zip(list(signals_qs), data['results']):
            self.assertEqual(signal.get_id_display(), signal_response_data['_display'])
            self.assertEqual(str(signal.uuid), signal_response_data['uuid'])
            self.assertEqual(signal.get_id_display(), signal_response_data['id_display'])
            self.assertEqual(signal.text, signal_response_data['text'])
            if signal.status.state in [AFGEHANDELD, GEANNULEERD, GESPLITST, ]:
                self.assertEqual('CLOSED', signal_response_data['status']['state'])
                self.assertEqual('Afgesloten', signal_response_data['status']['state_display'])
            else:
                self.assertEqual('OPEN', signal_response_data['status']['state'])
                self.assertEqual('Open', signal_response_data['status']['state_display'])


class TestMySignalsListEndpointDisabled(APITestCase):
    endpoint = '/my/signals/'

    def setUp(self):
        SignalFactoryWithImage.create_batch(5, reporter__email='my-signals-test-reporter@example.com')
        token = Token.objects.create(reporter_email='my-signals-test-reporter@example.com')
        self.request_headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

    def test_my_signals_feature_disabled(self):
        response = self.client.get(self.endpoint, **self.request_headers)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
