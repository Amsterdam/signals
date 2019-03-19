from datetime import datetime, timedelta

from django.test import TestCase, override_settings
from freezegun import freeze_time

from signals.apps.sigmax.tasks import _get_stuck_sending_signals, _set_signals_to_failed
from signals.apps.signals import workflow
from signals.apps.signals.models import Status
from tests.apps.signals.factories import SignalFactory


class TestFailStuckSendingSignalsTask(TestCase):
    old_signals = []
    new_signals = []

    def setUp(self):
        self.old_signals = []
        self.new_signals = []
        time = datetime.utcnow() - timedelta(minutes=30)

        # Create 5 signals with status TE_VERZENDEN 30 minutes in the past
        with freeze_time(time):
            for _ in range(5):
                signal = SignalFactory.create()
                status = Status(_signal=signal, state=workflow.TE_VERZENDEN)
                status.save()
                signal.status = status
                signal.save()
                self.old_signals.append(signal)

        # Create 5 signals with status TE_VERZENDEN in the future
        time = datetime.utcnow() + timedelta(minutes=30)
        with freeze_time(time):
            for _ in range(5):
                signal = SignalFactory.create()
                status = Status(_signal=signal, state=workflow.TE_VERZENDEN)
                status.save()
                signal.status = status
                signal.save()
                self.new_signals.append(signal)

    @override_settings(SIGMAX_SEND_FAIL_TIMEOUT_MINUTES=15)
    def test_get_stuck_sending_signals(self):
        stuck_signals = _get_stuck_sending_signals(datetime.now())
        self.assertEqual(5, stuck_signals.count())

        stuck_signal_ids = [signal.id for signal in stuck_signals]
        old_signal_ids = [signal.id for signal in self.old_signals]
        new_signal_ids = [signal.id for signal in self.new_signals]

        self.assertEqual(set(old_signal_ids), set(stuck_signal_ids))

        for signal_id in new_signal_ids:
            self.assertTrue(signal_id not in stuck_signal_ids)

    def test_set_signals_to_failed(self):
        _set_signals_to_failed(self.old_signals)

        for signal in self.old_signals:
            signal.refresh_from_db()

            self.assertEqual(workflow.VERZENDEN_MISLUKT, signal.status.state)
