# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta

from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Signal
from tests.test import SuperUserMixin


class TestSignalContextView(SuperUserMixin, APITestCase):
    def setUp(self):
        now = timezone.now()

        self.reporter_1_email = 'reporter_1@example.com'
        self.reporter_2_email = 'reporter_2@example.com'

        with freeze_time(now - timedelta(days=5)):
            SignalFactory.create_batch(2, reporter__email=self.reporter_1_email, status__state=workflow.BEHANDELING)
            SignalFactory.create_batch(3, reporter__email=self.reporter_1_email, status__state=workflow.AFGEHANDELD)

        self.reporter_1_signals = Signal.objects.filter(reporter__email=self.reporter_1_email)

        FeedbackFactory.create(_signal=self.reporter_1_signals[0], submitted_at=now, is_satisfied=False)
        FeedbackFactory.create(_signal=self.reporter_1_signals[2], submitted_at=now, is_satisfied=False)
        FeedbackFactory.create(_signal=self.reporter_1_signals[4], submitted_at=now, is_satisfied=True)

        self.anonymous_signals = [SignalFactory.create(reporter__email=None, status__state=workflow.BEHANDELING),
                                  SignalFactory.create(reporter__email='', status__state=workflow.BEHANDELING)]
        self.reporter_2_signals = SignalFactory.create_batch(size=5, reporter__email=self.reporter_2_email)

    def test_get_signal_context(self):
        self.client.force_authenticate(user=self.superuser)

        signal_id = self.reporter_1_signals[0].pk
        response = self.client.get(f'/signals/v1/private/signals/{signal_id}/context/')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['geography']['signal_count'], 0)

        self.assertEqual(response_data['reporter']['signal_count'], 5)
        self.assertEqual(response_data['reporter']['open_count'], 2)
        self.assertEqual(response_data['reporter']['positive_count'], 1)
        self.assertEqual(response_data['reporter']['negative_count'], 2)

    def test_get_signal_context_reporter_detail(self):
        self.client.force_authenticate(user=self.superuser)

        signal_id = self.reporter_1_signals[1].pk
        response = self.client.get(f'/signals/v1/private/signals/{signal_id}/context/reporter/')
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['count'], 5)
        self.assertEqual(len(response_data['results']), 5)

    def test_get_signal_context_geography_detail(self):
        self.client.force_authenticate(user=self.superuser)

        signal_id = self.reporter_1_signals[2].pk
        response = self.client.get(f'/signals/v1/private/signals/{signal_id}/context/geography')
        self.assertEqual(response.status_code, 200)

    def test_get_anonymous_signals_context(self):
        self.client.force_authenticate(user=self.superuser)

        for signal in self.anonymous_signals:
            response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/context/')
            self.assertEqual(response.status_code, 200)

            response_data = response.json()
            self.assertEqual(response_data['geography']['signal_count'], 0)

            self.assertEqual(response_data['reporter']['signal_count'], 1)
            self.assertEqual(response_data['reporter']['open_count'], 1)
            self.assertEqual(response_data['reporter']['positive_count'], 0)
            self.assertEqual(response_data['reporter']['negative_count'], 0)

    def test_get_anonymous_signals_context_reporter_detail(self):
        self.client.force_authenticate(user=self.superuser)

        for signal in self.anonymous_signals:
            response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/context/reporter/')
            self.assertEqual(response.status_code, 200)

            response_data = response.json()
            self.assertEqual(response_data['count'], 0)
            self.assertEqual(len(response_data['results']), 0)

    def test_get_anonymous_signals_context_geography_detail(self):
        self.client.force_authenticate(user=self.superuser)

        for signal in self.anonymous_signals:
            response = self.client.get(f'/signals/v1/private/signals/{signal.pk}/context/geography/')
            self.assertEqual(response.status_code, 200)
