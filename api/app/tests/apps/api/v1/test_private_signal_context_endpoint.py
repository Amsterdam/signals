# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from datetime import timedelta

from django.test.utils import override_settings
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Signal
from tests.test import SuperUserMixin


class ReporterContextDataMixin:
    def setUp(self):
        now = timezone.now()

        # Reporter and reported signals/complaints for this test
        self.reporter_a_email = 'reporter_a@example.com'
        self.n_open_a = 4
        self.n_unhappy_a = 2
        self.n_closed_a = 3

        with freeze_time(now - timedelta(days=7)):
            self.open_ = SignalFactory.create_batch(
                size=self.n_open_a, reporter__email=self.reporter_a_email, status__state=workflow.BEHANDELING)
            self.closed = SignalFactory.create_batch(
                size=self.n_closed_a, reporter__email=self.reporter_a_email, status__state=workflow.AFGEHANDELD)
            self.unhappy = SignalFactory.create_batch(
                size=self.n_unhappy_a, reporter__email=self.reporter_a_email, status__state=workflow.AFGEHANDELD)

        for i, signal in enumerate(self.unhappy):
            with freeze_time(now - timedelta(hours=i)):
                FeedbackFactory.create(_signal=signal, submitted_at=now, is_satisfied=False)

        for i, signal in enumerate(self.closed):
            with freeze_time(now - timedelta(hours=i)):
                FeedbackFactory.create(_signal=signal, submitted_at=None, is_satisfied=None)

        # Some other signals that should not be selected
        SignalFactory.create_batch(size=5, reporter__email='reporter_b@example.com')

        self.anonymous_signal_1 = SignalFactory.create(reporter__email=None)
        self.anonymous_signal_2 = SignalFactory.create(reporter__email='')


class TestReporterContextReporterBrief(ReporterContextDataMixin, APITestCase, SuperUserMixin):
    brief_endpoint = '/signals/v1/private/signals/{pk}/reporter_context_brief'

    @override_settings(API_ENABLE_SIGNAL_REPORTER_CONTEXT=False)
    def test_reporter_context_brief_disabled(self):
        start = Signal.objects.filter(reporter__email__exact=self.reporter_a_email).first()
        url = self.brief_endpoint.format(pk=start.id)

        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_settings(API_ENABLE_SIGNAL_REPORTER_CONTEXT=True)
    def test_anonymous_signals(self):
        self.client.force_authenticate(user=self.superuser)

        url = self.brief_endpoint.format(pk=self.anonymous_signal_1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

        url = self.brief_endpoint.format(pk=self.anonymous_signal_2.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    @override_settings(API_ENABLE_SIGNAL_REPORTER_CONTEXT=True)
    def test_reporter_context_brief(self):
        start = Signal.objects.filter(reporter__email__exact=self.reporter_a_email).first()
        url = self.brief_endpoint.format(pk=start.id)

        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['signal_count'], self.n_open_a + self.n_unhappy_a + self.n_closed_a)
        self.assertEqual(response_json['negative_count'], self.n_unhappy_a)
        self.assertEqual(response_json['open_count'], self.n_open_a)


class TestReporterContext(ReporterContextDataMixin, APITestCase, SuperUserMixin):
    endpoint = '/signals/v1/private/signals/{pk}/reporter_context/'

    @override_settings(API_ENABLE_SIGNAL_REPORTER_CONTEXT=False)
    def test_reporter_context_disabled(self):
        start = Signal.objects.filter(reporter__email__exact=self.reporter_a_email).first()
        url = self.endpoint.format(pk=start.id)

        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_settings(API_ENABLE_SIGNAL_REPORTER_CONTEXT=True)
    def test_anonymous_signals(self):
        self.client.force_authenticate(user=self.superuser)

        url = self.endpoint.format(pk=self.anonymous_signal_1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

        url = self.endpoint.format(pk=self.anonymous_signal_2.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    @override_settings(API_ENABLE_SIGNAL_REPORTER_CONTEXT=True)
    def test_reporter_context(self):
        start = Signal.objects.filter(reporter__email__exact=self.reporter_a_email).first()
        url = self.endpoint.format(pk=start.id)

        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertIn('results', response_json)
        self.assertEqual(response_json['count'], self.n_open_a + self.n_unhappy_a + self.n_closed_a)
