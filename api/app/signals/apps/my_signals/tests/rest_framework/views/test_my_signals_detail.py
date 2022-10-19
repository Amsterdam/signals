# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.test import override_settings
from django.urls import include, path
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase

from signals.apps.api.views import NamespaceView
from signals.apps.my_signals.models import Token
from signals.apps.signals.factories import AttachmentFactory, SignalFactory, StatusFactory
from signals.apps.signals.workflow import AFGEHANDELD

urlpatterns = [
    path('v1/relations/', NamespaceView.as_view(), name='signal-namespace'),
    path('', include('signals.apps.my_signals.urls')),
]


class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns


@override_settings(ROOT_URLCONF=test_urlconf)
class TestMySignalsDetailEndpoint(APITestCase):
    endpoint = '/my/signals'

    def setUp(self):
        self.signal = SignalFactory.create(reporter__email='my-signals-test-reporter@example.com')
        AttachmentFactory.create_batch(3, _signal=self.signal)

        token = Token.objects.create(reporter_email='my-signals-test-reporter@example.com')
        self.request_headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

    def test_my_signal(self):
        """
        Normal signals can be retrieved
        """
        response = self.client.get(f'{self.endpoint}/{self.signal.uuid}', **self.request_headers)
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

        response = self.client.get(f'{self.endpoint}/{self.signal.uuid}', **self.request_headers)
        self.assertEqual(response.status_code, HTTP_200_OK)

        response_data = response.json()
        self.assertEqual('CLOSED', response_data['status']['state'])
        self.assertEqual('Afgesloten', response_data['status']['state_display'])

    def test_my_signal_parent(self):
        """
        Parent signals can be retrieved
        """
        signal = SignalFactory.create(reporter__email='my-signals-test-reporter@example.com')
        SignalFactory.create(parent=signal)

        response = self.client.get(f'{self.endpoint}/{signal.uuid}', **self.request_headers)
        self.assertEqual(response.status_code, HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(signal.get_id_display(), response_data['_display'])
        self.assertEqual(str(signal.uuid), response_data['uuid'])
        self.assertEqual(signal.get_id_display(), response_data['id_display'])
        self.assertEqual(signal.text, response_data['text'])
        self.assertEqual('OPEN', response_data['status']['state'])
        self.assertEqual('Open', response_data['status']['state_display'])
        self.assertEqual(signal.location.address['postcode'], response_data['location']['address']['postcode'])
        self.assertEqual(signal.location.address['huisnummer'], response_data['location']['address']['huisnummer'])
        self.assertEqual(signal.location.address['woonplaats'],
                         response_data['location']['address']['woonplaats'])
        self.assertEqual(signal.location.address['openbare_ruimte'],
                         response_data['location']['address']['openbare_ruimte'])
        self.assertEqual(signal.location.address_text, response_data['location']['address_text'])
        self.assertEqual('Point', response_data['location']['geometrie']['type'])
        self.assertIn(signal.location.geometrie[0], response_data['location']['geometrie']['coordinates'])
        self.assertIn(signal.location.geometrie[1], response_data['location']['geometrie']['coordinates'])
        self.assertEqual({}, response_data['extra_properties'])

    def test_my_signal_children(self):
        """
        Child signals cannot be retrieved
        """
        parent = SignalFactory.create(reporter__email='my-signals-test-reporter@example.com')
        signal = SignalFactory.create(parent=parent, reporter__email='my-signals-test-reporter@example.com')

        response = self.client.get(f'{self.endpoint}/{signal.uuid}', **self.request_headers)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_my_signals_feature_401(self):
        response = self.client.get(f'{self.endpoint}/{self.signal.uuid}', HTTP_AUTHORIZATION='INVALID-TOKEN')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)


class TestMySignalsDetailEndpointDisabled(APITestCase):
    endpoint = '/my/signals'

    def setUp(self):
        self.signal = SignalFactory.create(reporter__email='my-signals-test-reporter@example.com')
        AttachmentFactory.create_batch(3, _signal=self.signal)

        token = Token.objects.create(reporter_email='my-signals-test-reporter@example.com')
        self.request_headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

    def test_my_signals_feature_disabled(self):
        response = self.client.get(f'{self.endpoint}/{self.signal.uuid}', **self.request_headers)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        response = self.client.get(f'{self.endpoint}/{self.signal.uuid}')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
