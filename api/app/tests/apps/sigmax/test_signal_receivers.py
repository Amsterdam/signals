from unittest import mock

from django.test import TestCase

from signals.apps.signals.managers import update_status
from tests.apps.signals.factories import SignalFactory, StatusFactory


class TestSignalReceivers(TestCase):

    @mock.patch('signals.apps.sigmax.signal_receivers.tasks', autospec=True)
    def test_status_update_handler(self, mocked_tasks):
        signal = SignalFactory.create()
        prev_status = signal.status

        new_status = StatusFactory.create(_signal=signal)
        signal.status = new_status
        signal.save()

        update_status.send_robust(
            sender=self.__class__,
            signal_obj=signal,
            status=new_status,
            prev_status=prev_status,
        )

        mocked_tasks.push_to_sigmax.delay.assert_called_once_with(pk=signal.id)
