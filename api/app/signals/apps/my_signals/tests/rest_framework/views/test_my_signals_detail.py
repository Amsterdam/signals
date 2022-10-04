# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import copy

from django.conf import settings
from django.test import override_settings
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase

from signals.apps.signals.factories import AttachmentFactory, SignalFactory, StatusFactory
from signals.apps.signals.workflow import AFGEHANDELD


class TestMySignalsDetailEndpoint(APITestCase):
    endpoint = '/signals/v1/my/signals'

    def setUp(self):
        self.feature_flags_enabled = settings.FEATURE_FLAGS
        self.feature_flags_enabled['MY_SIGNALS_ENABLED'] = True

        self.feature_flags_disabled = copy.deepcopy(self.feature_flags_enabled)
        self.feature_flags_disabled['MY_SIGNALS_ENABLED'] = False

        self.signal = SignalFactory.create()
        AttachmentFactory.create_batch(3, _signal=self.signal)

    def test_my_signal(self):
        with override_settings(FEATURE_FLAGS=self.feature_flags_enabled):
            response = self.client.get(f'{self.endpoint}/{self.signal.uuid}')
            self.assertEqual(response.status_code, HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(self.signal.get_id_display(), response_data['_display'])
        self.assertEqual(str(self.signal.uuid), response_data['uuid'])
        self.assertEqual(self.signal.get_id_display(), response_data['id_display'])
        self.assertEqual(self.signal.text, response_data['text'])
        self.assertEqual('OPEN', response_data['status']['state'])
        self.assertEqual('Open', response_data['status']['state_display'])
        self.assertEqual(self.signal.location.address['postcode'], response_data['location']['address']['postcode'])
        self.assertEqual(self.signal.location.address['huisnummer'], response_data['location']['address']['huisnummer'])
        self.assertEqual(self.signal.location.address['woonplaats'],
                         response_data['location']['address']['woonplaats'])
        self.assertEqual(self.signal.location.address['openbare_ruimte'],
                         response_data['location']['address']['openbare_ruimte'])
        self.assertEqual(self.signal.location.address_text, response_data['location']['address_text'])
        self.assertEqual('Point', response_data['location']['geometrie']['type'])
        self.assertIn(self.signal.location.geometrie[0], response_data['location']['geometrie']['coordinates'])
        self.assertIn(self.signal.location.geometrie[1], response_data['location']['geometrie']['coordinates'])
        self.assertEqual({}, response_data['extra_properties'])

        # Update the status to a "CLOSED" state
        status = StatusFactory.create(_signal=self.signal, state=AFGEHANDELD)
        self.signal.status = status
        self.signal.save()

        with override_settings(FEATURE_FLAGS=self.feature_flags_enabled):
            response = self.client.get(f'{self.endpoint}/{self.signal.uuid}')
            self.assertEqual(response.status_code, HTTP_200_OK)

        response_data = response.json()
        self.assertEqual('CLOSED', response_data['status']['state'])
        self.assertEqual('Afgesloten', response_data['status']['state_display'])

    def test_my_signals_feature_disabled(self):
        with override_settings(FEATURE_FLAGS=self.feature_flags_disabled):
            response = self.client.get(f'{self.endpoint}/{self.signal.uuid}')
            self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
