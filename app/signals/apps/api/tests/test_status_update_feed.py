# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from django.contrib.auth.models import Permission
from django.test import override_settings

from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Status
from signals.apps.users.factories import UserFactory
from signals.test.utils import SignalsBaseApiTestCase


@override_settings(
    STATUS_UPDATE_FEED_ALLOWED_SOURCES=('mobile-app',),
    STATUS_UPDATE_FEED_MAX_PAGE_SIZE=20,
)
class TestStatusUpdateFeed(SignalsBaseApiTestCase):
    endpoint = '/signals/v1/private/status-updates'
    source = 'mobile-app'

    def setUp(self):
        self.integration_user = UserFactory.create()
        self.read_permission = Permission.objects.get(codename='sia_read')
        self.status_update_permission = Permission.objects.get(codename='sia_status_updates_read')
        self.integration_user.user_permissions.add(self.read_permission, self.status_update_permission)
        self.client.force_authenticate(user=self.integration_user)

    def test_authentication_is_required(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.endpoint, {'source': self.source})

        self.assertEqual(response.status_code, 401)

    def test_dedicated_permission_is_required(self):
        user = UserFactory.create()
        user.user_permissions.add(self.read_permission)
        self.client.force_authenticate(user=user)

        get_response = self.client.get(self.endpoint, {'source': self.source})
        head_response = self.client.head(self.endpoint, {'source': self.source})

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(head_response.status_code, 403)

    def test_read_permission_is_required(self):
        user = UserFactory.create()
        user.user_permissions.add(self.status_update_permission)
        self.client.force_authenticate(user=user)

        get_response = self.client.get(self.endpoint, {'source': self.source})
        head_response = self.client.head(self.endpoint, {'source': self.source})

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(head_response.status_code, 403)

    def test_source_is_required_and_must_be_enabled(self):
        missing_source_response = self.client.get(self.endpoint)
        disabled_source_response = self.client.get(self.endpoint, {'source': 'other-source'})

        self.assertEqual(missing_source_response.status_code, 400)
        self.assertEqual(disabled_source_response.status_code, 403)

    def test_only_supported_statuses_and_fields_are_returned(self):
        signal = SignalFactory.create(source=self.source)
        status_mapping = [
            (workflow.BEHANDELING, 'IN_PROGRESS'),
            (workflow.INGEPLAND, 'IN_PROGRESS'),
            (workflow.ON_HOLD, 'IN_PROGRESS'),
            (workflow.DOORGEZET_NAAR_EXTERN, 'IN_PROGRESS'),
            (workflow.TE_VERZENDEN, 'IN_PROGRESS'),
            (workflow.VERZONDEN, 'IN_PROGRESS'),
            (workflow.AFGEHANDELD_EXTERN, 'IN_PROGRESS'),
            (workflow.VERZOEK_TOT_AFHANDELING, 'IN_PROGRESS'),
            (workflow.REACTIE_ONTVANGEN, 'IN_PROGRESS'),
            (workflow.HEROPEND, 'IN_PROGRESS'),
            (workflow.AFGEHANDELD, 'RESOLVED'),
            (workflow.GEANNULEERD, 'CANCELLED'),
        ]
        expected_statuses = []
        for state, _ in status_mapping:
            expected_statuses.append(Status.objects.create(
                _signal=signal,
                state=state,
                text='Internal note',
                user='handler@example.com',
                extra_properties={'internal': 'value'},
            ))

        response = self.client.get(self.endpoint, {'source': self.source})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            [item['status'] for item in body['items']],
            [expected_status for _, expected_status in status_mapping],
        )
        self.assertEqual([item['event_id'] for item in body['items']], [row.pk for row in expected_statuses])
        self.assertEqual(body['next_cursor'], expected_statuses[-1].pk)
        for item in body['items']:
            self.assertEqual(set(item), {'signal_id', 'status', 'changed_at', 'event_id'})
            self.assertEqual(item['signal_id'], str(signal.uuid))

    def test_feed_is_filtered_by_source_and_cursor(self):
        signal = SignalFactory.create(source=self.source)
        other_signal = SignalFactory.create(source='other-source')
        first = Status.objects.create(_signal=signal, state=workflow.BEHANDELING)
        other = Status.objects.create(_signal=other_signal, state=workflow.AFGEHANDELD, text='Resolved')

        first_response = self.client.get(self.endpoint, {'source': self.source})
        after_first_response = self.client.get(self.endpoint, {'source': self.source, 'after': first.pk})

        self.assertEqual([item['event_id'] for item in first_response.json()['items']], [first.pk])
        self.assertEqual(first_response.json()['next_cursor'], first.pk)
        self.assertEqual(after_first_response.json(), {'items': [], 'next_cursor': first.pk})

        later = Status.objects.create(_signal=signal, state=workflow.HEROPEND, text='Reopened')
        later_response = self.client.get(self.endpoint, {'source': self.source, 'after': first.pk})

        self.assertEqual([item['event_id'] for item in later_response.json()['items']], [later.pk])
        self.assertNotEqual(other.pk, later_response.json()['next_cursor'])
        self.assertEqual(later_response.json()['next_cursor'], later.pk)

    def test_cursor_advances_over_statuses_that_are_not_returned(self):
        signal = SignalFactory.create(source=self.source)
        initial_cursor = signal.status.pk
        hidden_statuses = [
            workflow.GEMELD,
            workflow.AFWACHTING,
            workflow.REACTIE_GEVRAAGD,
            workflow.VERZENDEN_MISLUKT,
            workflow.GESPLITST,
            workflow.VERZOEK_TOT_HEROPENEN,
        ]
        hidden_rows = [
            Status.objects.create(_signal=signal, state=state)
            for state in hidden_statuses
        ]
        in_progress = Status.objects.create(_signal=signal, state=workflow.BEHANDELING)

        cursor = initial_cursor
        for hidden_row in hidden_rows:
            response = self.client.get(self.endpoint, {
                'source': self.source,
                'after': cursor,
                'limit': 1,
            })
            self.assertEqual(response.json(), {'items': [], 'next_cursor': hidden_row.pk})
            cursor = hidden_row.pk

        visible_response = self.client.get(self.endpoint, {
            'source': self.source,
            'after': cursor,
            'limit': 1,
        })
        self.assertEqual(visible_response.json()['items'][0]['event_id'], in_progress.pk)
        self.assertEqual(visible_response.json()['next_cursor'], in_progress.pk)

    def test_cursor_and_limit_are_validated(self):
        invalid_cursor_response = self.client.get(self.endpoint, {'source': self.source, 'after': -1})
        invalid_limit_response = self.client.get(self.endpoint, {'source': self.source, 'limit': 21})

        self.assertEqual(invalid_cursor_response.status_code, 400)
        self.assertEqual(invalid_limit_response.status_code, 400)
