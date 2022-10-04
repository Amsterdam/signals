# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import copy

from django.conf import settings
from django.test import override_settings
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase

from signals.apps.signals.factories import SignalFactoryWithImage
from signals.apps.signals.models import Signal
from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD, GESPLITST


class TestMySignalsListEndpoint(APITestCase):
    endpoint = '/signals/v1/my/signals/'

    def setUp(self):
        self.feature_flags_enabled = settings.FEATURE_FLAGS
        self.feature_flags_enabled['MY_SIGNALS_ENABLED'] = True

        self.feature_flags_disabled = copy.deepcopy(self.feature_flags_enabled)
        self.feature_flags_disabled['MY_SIGNALS_ENABLED'] = False

        SignalFactoryWithImage.create_batch(5)
        SignalFactoryWithImage.create_batch(5, status__state=AFGEHANDELD)

    def test_my_signals(self):
        with override_settings(FEATURE_FLAGS=self.feature_flags_enabled):
            response = self.client.get(self.endpoint)
            self.assertEqual(response.status_code, HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data['results']), Signal.objects.count())

        signals_qs = Signal.objects.order_by('-created_at')

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

    def test_my_signals_feature_disabled(self):
        with override_settings(FEATURE_FLAGS=self.feature_flags_disabled):
            response = self.client.get(self.endpoint)
            self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
