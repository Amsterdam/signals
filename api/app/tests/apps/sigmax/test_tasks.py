from datetime import timedelta

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.sigmax.tasks import fail_stuck_sending_signals
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal, Status
from tests.apps.signals.factories import SignalFactory


class TestFailStuckSendingSignalsTask(TestCase):
    def setUp(self):
        now = timezone.now()
        with(freeze_time(now)):
            SignalFactory.create_batch(
                5, status__state=workflow.TE_VERZENDEN, status__target_api=Status.TARGET_API_SIGMAX
            )

        past = now - timedelta(hours=48)
        with(freeze_time(past)):
            SignalFactory.create_batch(
                5, status__state=workflow.TE_VERZENDEN, status__target_api=Status.TARGET_API_SIGMAX
            )

    def test_fail_stuck_sending_signals(self):
        qs = Signal.objects.all()

        self.assertEqual(qs.filter(status__state=workflow.TE_VERZENDEN).count(), 10)

        fail_stuck_sending_signals()

        self.assertEqual(qs.filter(status__state=workflow.TE_VERZENDEN).count(), 5)
        self.assertEqual(qs.filter(status__state=workflow.VERZENDEN_MISLUKT).count(), 5)

        text = 'Melding stond langer dan {} minuten op TE_VERZENDEN. Mislukt'.format(
            settings.SIGMAX_SEND_FAIL_TIMEOUT_MINUTES
        )
        for signal in qs.filter(status__state=workflow.VERZENDEN_MISLUKT):
            self.assertEqual(signal.status.text, text)
