# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.test.utils import freeze_time
from django.utils import timezone
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)
from rest_framework.test import APITestCase

from signals.apps.email_integrations.factories import EmailTemplateFactory
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.signals.factories import ReporterFactory, SignalFactory
from signals.apps.signals.models import Reporter
from signals.apps.users.factories import UserFactory
from signals.test.utils import SIAReadWriteUserMixin


class TestPrivateSignalReportersEndpointUnAuthorized(APITestCase):
    def setUp(self) -> None:
        self.signal = SignalFactory.create()

    def test_list(self) -> None:
        response = self.client.get(f'/signals/v1/private/signals/{self.signal.pk}/reporters/')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_create(self) -> None:
        response = self.client.post(f'/signals/v1/private/signals/{self.signal.pk}/reporters/', data={})
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)


class TestPrivateSignalReportersEndpoint(SIAReadWriteUserMixin, APITestCase):
    def setUp(self) -> None:
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))
        self.sia_read_write_user.user_permissions.add(Permission.objects.get(codename='sia_can_view_contact_details'))

        self.client.force_authenticate(user=self.sia_read_write_user)

    def test_list(self) -> None:
        signal = SignalFactory.create()

        now = timezone.now()
        for i in range(1, 5):
            with freeze_time(now + timedelta(hours=i)):
                ReporterFactory.create(_signal=signal)

        response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/reporters/')
        self.assertEqual(response.status_code, HTTP_200_OK)

        response_json = response.json()
        self.assertEqual(response_json['count'], 5)
        self.assertEqual(len(response_json['results']), 5)

    def test_create_missing_sharing_allowed_field(self) -> None:
        signal = SignalFactory.create()

        response = self.client.post(
            f'/signals/v1/private/signals/{signal.pk}/reporters/',
            data={'email': 'test@example.com', 'phone': '0612345678', },
            format='json'
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_can_create(self) -> None:
        EmailTemplateFactory.create(key=EmailTemplate.VERIFY_EMAIL_REPORTER)
        EmailTemplateFactory.create(key=EmailTemplate.NOTIFY_CURRENT_REPORTER)
        signal = SignalFactory.create(reporter__state=Reporter.REPORTER_STATE_APPROVED)

        response = self.client.post(
            f'/signals/v1/private/signals/{signal.pk}/reporters/',
            data={'email': 'test@example.com', 'phone': '0612345678', 'sharing_allowed': True},
            format='json'
        )

        self.assertEqual(response.status_code, HTTP_201_CREATED)

        reporter = response.json()
        self.assertEqual(reporter.get('state'), Reporter.REPORTER_STATE_VERIFICATION_EMAIL_SENT)

    def test_can_cancel_without_reason(self) -> None:
        signal = SignalFactory.create(reporter__state=Reporter.REPORTER_STATE_APPROVED)
        reporter = ReporterFactory.create(_signal=signal, state=Reporter.REPORTER_STATE_VERIFICATION_EMAIL_SENT)

        response = self.client.post(
            f'/signals/v1/private/signals/{signal.pk}/reporters/{reporter.pk}/cancel',
            data={},
            format='json',
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json().get('state'), Reporter.REPORTER_STATE_CANCELLED)

        log = reporter.history_log.all()[0]
        self.assertEqual(log.what, 'UPDATE_REPORTER')
        self.assertEqual(log.description, 'Contactgegevens wijziging geannuleerd.')

    def test_can_cancel_with_reason(self) -> None:
        signal = SignalFactory.create(reporter__state=Reporter.REPORTER_STATE_APPROVED)
        reporter = ReporterFactory.create(_signal=signal, state=Reporter.REPORTER_STATE_VERIFICATION_EMAIL_SENT)

        reason = 'Wijziging aangevraagd door buurman.'

        response = self.client.post(
         f'/signals/v1/private/signals/{signal.pk}/reporters/{reporter.pk}/cancel',
         data={'reason': reason},
         format='json',
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json().get('state'), Reporter.REPORTER_STATE_CANCELLED)

        log = reporter.history_log.all()[0]
        self.assertEqual(log.what, 'UPDATE_REPORTER')
        self.assertEqual(log.description, f'Contactgegevens wijziging geannuleerd: {reason}')

    def test_404_when_signal_not_found(self) -> None:
        response = self.client.post(
            '/signals/v1/private/signals/11145/reporters/1/cancel',
            data={},
            format='json',
        )

        self.assertEqual(response.status_code, 404)

    def test_404_when_reporter_not_found(self) -> None:
        signal = SignalFactory.create(reporter__state=Reporter.REPORTER_STATE_APPROVED)

        response = self.client.post(
            f'/signals/v1/private/signals/{signal.pk}/reporters/11145/cancel',
            data={},
            format='json',
        )

        self.assertEqual(response.status_code, 404)

    def test_400_when_transition_not_allowed(self) -> None:
        signal = SignalFactory.create(reporter__state=Reporter.REPORTER_STATE_APPROVED)

        response = self.client.post(
            f'/signals/v1/private/signals/{signal.pk}/reporters/{signal.reporter.pk}/cancel',
            data={},
            format='json',
        )

        self.assertEqual(response.status_code, 400)

        body = response.json()
        non_field_errors = body.get('non_field_errors')
        self.assertIsNotNone(non_field_errors)
        self.assertEqual(len(non_field_errors), 1)
        self.assertEqual(non_field_errors[0], 'Cancelling this reporter is not possible.')

    def test_403_forbidden(self):
        """
        A user without the permission "sia_can_view_contact_details" should not be allowed to create a new Reporter OR
        update a transition to a new Reporter.
        """
        user_incorrect_permissions = UserFactory.create()
        user_incorrect_permissions.user_permissions.add(self.sia_read)
        user_incorrect_permissions.user_permissions.add(self.sia_write)
        user_incorrect_permissions.user_permissions.add(Permission.objects.get(codename='sia_can_view_all_categories'))

        self.client.force_authenticate(user_incorrect_permissions)

        signal = SignalFactory.create(reporter__state=Reporter.REPORTER_STATE_APPROVED)

        # Create
        response = self.client.post(
            f'/signals/v1/private/signals/{signal.pk}/reporters/',
            data={'email': 'test@example.com', 'phone': '0612345678', 'sharing_allowed': True},
            format='json'
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Cancel, signal not found
        response = self.client.post(
            '/signals/v1/private/signals/11145/reporters/1/cancel',
            data={},
            format='json',
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Cancel, reporter not found
        response = self.client.post(
            f'/signals/v1/private/signals/{signal.pk}/reporters/11145/cancel',
            data={},
            format='json',
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Cancel
        response = self.client.post(
            f'/signals/v1/private/signals/{signal.pk}/reporters/{signal.reporter.pk}/cancel',
            data={},
            format='json',
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
