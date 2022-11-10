# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import copy
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import override_settings
from django.urls import include, path
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase

from signals.apps.api.views import NamespaceView
from signals.apps.my_signals.models import Token
from signals.apps.signals import workflow
from signals.apps.signals.factories import (
    CategoryAssignmentFactory,
    LocationFactory,
    NoteFactory,
    PriorityFactory,
    ReporterFactory,
    SignalFactoryWithImage,
    StatusFactory,
    TypeFactory
)
from signals.apps.signals.models import Signal

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
        self.feature_flags = copy.deepcopy(settings.FEATURE_FLAGS)
        self.feature_flags.update({'SIGNAL_HISTORY_LOG_ENABLED': True})

        token = Token.objects.create(reporter_email='my-signals-test-reporter@example.com')
        self.request_headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

    def _create_initial_signal(self):
        now = timezone.now()
        with freeze_time(now - timezone.timedelta(minutes=7)):
            signal = Signal.objects.create(text='Test melding (My Signals)', incident_date_start=now)

        with freeze_time(now - timezone.timedelta(minutes=6)):
            status = StatusFactory.create(_signal=signal)

        with freeze_time(now - timezone.timedelta(minutes=5)):
            location = LocationFactory.create(_signal=signal)

        with freeze_time(now - timezone.timedelta(minutes=4)):
            category_assignment = CategoryAssignmentFactory.create(_signal=signal)

        with freeze_time(now - timezone.timedelta(minutes=3)):
            reporter = ReporterFactory.create(email='my-signals-test-reporter@example.com')

        with freeze_time(now - timezone.timedelta(minutes=2)):
            priority = PriorityFactory.create(_signal=signal)

        with freeze_time(now - timezone.timedelta(minutes=1)):
            _type = TypeFactory.create(_signal=signal)

        signal.status = status
        signal.location = location
        signal.category_assignment = category_assignment
        signal.reporter = reporter
        signal.priority = priority
        signal.type_assignment = _type

        signal.save()

        # A bit hacky but this makes sure the history is present
        call_command('migrate_signals_history', stdout=StringIO())

        return signal

    def _create_signal_with_history(self):
        now = timezone.now()
        with freeze_time(now - timezone.timedelta(minutes=113)):
            # Initial Signal is created 2 hours ago
            signal = self._create_initial_signal()

        # Simulate workflow
        with freeze_time(now - timezone.timedelta(minutes=110)):
            status = StatusFactory(state=workflow.BEHANDELING, text=None, _signal=signal)
            signal.status = status
            signal.save()

        with freeze_time(now - timezone.timedelta(minutes=105)):
            status = StatusFactory(state=workflow.REACTIE_GEVRAAGD, text='Weet u meer?', _signal=signal)
            signal.status = status
            signal.save()

        with freeze_time(now - timezone.timedelta(minutes=60)):
            status = StatusFactory(state=workflow.REACTIE_ONTVANGEN, text='Ik heb alles gemeld', _signal=signal)
            signal.status = status
            signal.save()

        with freeze_time(now - timezone.timedelta(minutes=50)):
            category_assignment = CategoryAssignmentFactory(_signal=signal)
            priority = PriorityFactory(priority='high', _signal=signal)
            NoteFactory(text='Intern contact gehad en category aangepast + prio naar hoog', _signal=signal)
            status = StatusFactory(state=workflow.INGEPLAND, text=None, _signal=signal)
            signal.category_assignment = category_assignment
            signal.priority = priority
            signal.status = status
            signal.save()

        with freeze_time(now - timezone.timedelta(minutes=45)):
            priority = PriorityFactory(priority='normal', _signal=signal)
            NoteFactory(text='Prio weer naar normaal', _signal=signal)
            signal.priority = priority
            signal.save()

        with freeze_time(now - timezone.timedelta(minutes=30)):
            status = StatusFactory(state=workflow.AFGEHANDELD, text=None, _signal=signal)
            signal.status = status
            signal.save()

        with freeze_time(now - timezone.timedelta(minutes=20)):
            status = StatusFactory(state=workflow.HEROPEND, text='Melding nog niet AFGEHANDELD', _signal=signal)
            signal.status = status
            signal.save()

        with freeze_time(now - timezone.timedelta(minutes=15)):
            status = StatusFactory(state=workflow.REACTIE_GEVRAAGD, text='Toch nog 1 vraag, ok?', _signal=signal)
            signal.status = status
            signal.save()

        with freeze_time(now - timezone.timedelta(minutes=5)):
            status = StatusFactory(state=workflow.AFGEHANDELD, text='Melder heeft gebeld, medling AFGEHANDELD',
                                   _signal=signal)
            signal.status = status
            signal.save()

        # A bit hacky but this makes sure the history is present
        call_command('migrate_signals_history', stdout=StringIO())

        return signal

    def test_history_signal_created(self):
        signal = self._create_initial_signal()

        response = self.client.get(f'{self.endpoint}/{signal.uuid}/history', **self.request_headers)
        self.assertEqual(response.status_code, HTTP_200_OK)

        response_json = response.json()
        self.assertEqual(len(response_json), 2)

        self.assertEqual(response_json[0]['what'], 'UPDATE_SLA')
        self.assertEqual(response_json[0]['action'], 'Servicebelofte:')
        self.assertEqual(response_json[0]['description'], f'{signal.category_assignment.stored_handling_message}')
        self.assertEqual(response_json[0]['_signal'], f'{signal.uuid}')

        self.assertEqual(response_json[1]['what'], 'UPDATE_STATUS')
        self.assertEqual(response_json[1]['action'], 'Status gewijzigd naar: Open')
        self.assertEqual(response_json[1]['description'], f'{signal.status.text}')
        self.assertEqual(response_json[1]['_signal'], f'{signal.uuid}')

        # Reverse order
        response = self.client.get(f'{self.endpoint}/{signal.uuid}/history', data={'ordering': 'created_at'},
                                   **self.request_headers)
        self.assertEqual(response.status_code, HTTP_200_OK)

        response_json = response.json()
        self.assertEqual(len(response_json), 2)

        self.assertEqual(response_json[0]['what'], 'UPDATE_STATUS')
        self.assertEqual(response_json[0]['action'], 'Status gewijzigd naar: Open')
        self.assertEqual(response_json[0]['description'], f'{signal.status.text}')
        self.assertEqual(response_json[0]['_signal'], f'{signal.uuid}')

        self.assertEqual(response_json[1]['what'], 'UPDATE_SLA')
        self.assertEqual(response_json[1]['action'], 'Servicebelofte:')
        self.assertEqual(response_json[1]['description'], f'{signal.category_assignment.stored_handling_message}')
        self.assertEqual(response_json[1]['_signal'], f'{signal.uuid}')

        # Filter on UPDATE_STATUS
        response = self.client.get(f'{self.endpoint}/{signal.uuid}/history', data={'what': 'UPDATE_STATUS'},
                                   **self.request_headers)
        self.assertEqual(response.status_code, HTTP_200_OK)

        response_json = response.json()
        self.assertEqual(len(response_json), 1)

        self.assertEqual(response_json[0]['what'], 'UPDATE_STATUS')
        self.assertEqual(response_json[0]['action'], 'Status gewijzigd naar: Open')
        self.assertEqual(response_json[0]['description'], f'{signal.status.text}')
        self.assertEqual(response_json[0]['_signal'], f'{signal.uuid}')

        # Filter on UPDATE_SLA
        response = self.client.get(f'{self.endpoint}/{signal.uuid}/history', data={'what': 'UPDATE_SLA'},
                                   **self.request_headers)
        self.assertEqual(response.status_code, HTTP_200_OK)

        response_json = response.json()
        self.assertEqual(len(response_json), 1)

        self.assertEqual(response_json[0]['what'], 'UPDATE_SLA')
        self.assertEqual(response_json[0]['action'], 'Servicebelofte:')
        self.assertEqual(response_json[0]['description'], f'{signal.category_assignment.stored_handling_message}')
        self.assertEqual(response_json[0]['_signal'], f'{signal.uuid}')

    def assert_what_in_data(self, what, data, pos=None):
        if pos:
            self.assertEqual(data[pos]['what'], what)
        else:
            self.assertIn(what, [item['what'] for item in data])

    def assert_action_in_data(self, action, data, pos=None):
        if pos:
            self.assertEqual(data[pos]['action'], action)
        else:
            self.assertIn(action, [item['action'] for item in data])

    def assert_description_in_data(self, description, data, pos=None):
        if pos:
            self.assertEqual(data[pos]['description'], description)
        else:
            self.assertIn(description, [item['description'] for item in data])

    def test_history_signal_flow(self):
        signal = self._create_signal_with_history()

        response = self.client.get(f'{self.endpoint}/{signal.uuid}/history', data={'ordering': 'created_at'},
                                   **self.request_headers)
        self.assertEqual(response.status_code, HTTP_200_OK)

        response_json = response.json()
        self.assertEqual(len(response_json), 9)

        self.assert_what_in_data('UPDATE_STATUS', response_json, 0)
        self.assert_what_in_data('UPDATE_SLA', response_json, 1)
        self.assert_what_in_data('UPDATE_STATUS', response_json, 2)
        self.assert_what_in_data('UPDATE_STATUS', response_json, 3)
        self.assert_what_in_data('UPDATE_STATUS', response_json, 4)
        self.assert_what_in_data('UPDATE_STATUS', response_json, 5)
        self.assert_what_in_data('UPDATE_STATUS', response_json, 6)
        self.assert_what_in_data('UPDATE_STATUS', response_json, 7)
        self.assert_what_in_data('UPDATE_STATUS', response_json, 8)

    def test_history_not_my_signal(self):
        not_my_signal = SignalFactoryWithImage.create(reporter__email='not-me@example.com')
        response = self.client.get(f'{self.endpoint}/{not_my_signal.uuid}/history', **self.request_headers)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)


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
