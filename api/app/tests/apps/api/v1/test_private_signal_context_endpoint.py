# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from datetime import timedelta

from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APITestCase

from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Signal
from tests.test import SuperUserMixin


class TestReporterContextReporterBrief(APITestCase, SuperUserMixin):
    brief_endpoint = '/signals/v1/private/signals/{pk}/reporter_context_brief'

    def setUp(self):
        now = timezone.now()

        # Reporter and reported signals/complaints for this test
        self.reporter_a_email = 'reporter_a@example.com'
        self.n_open_a = 4
        self.n_unhappy_a = 2
        self.n_closed_a = 3

        with freeze_time(now - timedelta(days=7)):
            SignalFactory.create_batch(
                size=self.n_open_a, reporter__email=self.reporter_a_email, status__state=workflow.BEHANDELING)
            SignalFactory.create_batch(
                size=self.n_closed_a, reporter__email=self.reporter_a_email, status__state=workflow.AFGEHANDELD)
            unhappy = SignalFactory.create_batch(
                size=self.n_unhappy_a, reporter__email=self.reporter_a_email, status__state=workflow.AFGEHANDELD)

        for i, signal in enumerate(unhappy):
            with freeze_time(now - timedelta(hours=i)):
                FeedbackFactory.create(_signal=signal, submitted_at=now, is_satisfied=False)

        # Some other signals that should not be selected
        SignalFactory.create_batch(size=5, reporter__email='reporter_b@example.com')

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


class TestReporterContext(APITestCase, SuperUserMixin):
    pass
