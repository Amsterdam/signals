# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from io import StringIO
from typing import Any
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from signals.apps.signals.workflow import TE_VERZENDEN, VERZENDEN_MISLUKT
from signals.settings import SIGMAX_SEND_FAIL_TIMEOUT_MINUTES


class TestFailStuckSendingSignals(TestCase):
    """
    Unit tests for the fail_stuck_sending_signals management command.
    """

    @mock.patch('signals.apps.sigmax.management.commands.fail_stuck_sending_signals.fail_stuck_sending_signals',
                autospec=True)
    def test_call_command(self, mocked_fail_stuck_sending_signals: Any) -> None:
        """
        Test the call_command function for the fail_stuck_sending_signals command.

        This test case ensures that the fail_stuck_sending_signals function is called
        when the fail_stuck_sending_signals command is executed using call_command.

        Mocked fail_stuck_sending_signals is used to assert its call.

        """
        buffer = StringIO()
        call_command('fail_stuck_sending_signals', stdout=buffer)
        output = buffer.getvalue()

        mocked_fail_stuck_sending_signals.assert_called_once()

        self.assertIn(f'Add status "{VERZENDEN_MISLUKT}" to Signals that are stuck in "{TE_VERZENDEN}" '
                      f'for at least {SIGMAX_SEND_FAIL_TIMEOUT_MINUTES} minutes', output)
        self.assertIn('Done!', output)
