# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam
from typing import Any
from unittest import mock

from django.test import TestCase

from signals.apps.signals.factories import SignalFactory, StatusFactory
from signals.apps.signals.managers import update_status
from signals.apps.signals.models import Status
from signals.apps.signals.workflow import TE_VERZENDEN


class TestSignalReceivers(TestCase):
    """
    Unit tests for signal receivers.
    """

    @mock.patch('signals.apps.sigmax.signal_receivers.tasks', autospec=True)
    def test_status_update_handler(self, mocked_tasks: Any) -> None:
        """
        Test the status update handler when the signal is applicable.

        This test case ensures that when the status of a signal is updated to a
        TE_VERZENDEN state with TARGET_API_SIGMAX target API, the push_to_sigmax
        task is scheduled for execution.

        Mocked tasks are used to assert the call to push_to_sigmax.delay.

        """
        signal = SignalFactory.create()
        prev_status = signal.status

        new_status = StatusFactory.create(_signal=signal, state=TE_VERZENDEN, target_api=Status.TARGET_API_SIGMAX)
        signal.status = new_status
        signal.save()

        update_status.send_robust(sender=self.__class__, signal_obj=signal, status=new_status, prev_status=prev_status)
        mocked_tasks.push_to_sigmax.delay.assert_called_once_with(signal_id=signal.id)

    @mock.patch('signals.apps.sigmax.signal_receivers.tasks', autospec=True)
    def test_status_update_handler_not_called(self, mocked_tasks: Any) -> None:
        """
        Test the status update handler when the signal is not applicable.

        This test case ensures that when the status of a signal is updated to a
        non-TE_VERZENDEN state or a non-TARGET_API_SIGMAX target API, the push_to_sigmax
        task is not scheduled for execution.

        Mocked tasks are used to assert that push_to_sigmax.delay is not called.

        """
        signal = SignalFactory.create()
        prev_status = signal.status

        new_status = StatusFactory.create(_signal=signal)
        signal.status = new_status
        signal.save()

        update_status.send_robust(sender=self.__class__, signal_obj=signal, status=new_status, prev_status=prev_status)
        mocked_tasks.push_to_sigmax.delay.assert_not_called()

        new_status = StatusFactory.create(_signal=signal, state=TE_VERZENDEN, target_api=Status.TARGET_API_GISIB)
        signal.status = new_status
        signal.save()

        update_status.send_robust(sender=self.__class__, signal_obj=signal, status=new_status, prev_status=prev_status)
        mocked_tasks.push_to_sigmax.delay.assert_not_called()
