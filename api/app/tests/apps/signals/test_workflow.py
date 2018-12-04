"""
Tests for the workflow module.

Note: the workflow is enforced in the actions API, these tests therefore use
that API.
"""
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TransactionTestCase

from signals.apps.signals import workflow
from signals.apps.signals.models import Signal, Status
from tests.apps.signals import factories

HAPPY_REOPEN_SCENARIO = [
    workflow.GEMELD,
    workflow.BEHANDELING,
    workflow.AFGEHANDELD,
    workflow.HEROPEND,
    workflow.ON_HOLD,
    workflow.GEANNULEERD,
    workflow.HEROPEND,
    workflow.AFGEHANDELD,
]

UNHAPPY_REOPEN_SCENARIO = [
    workflow.GEMELD,
    workflow.BEHANDELING,
    workflow.ON_HOLD,
    workflow.BEHANDELING,
    workflow.HEROPEND,
    workflow.BEHANDELING,
]


class TestReopen(TransactionTestCase):
    def setUp(self):
        # We start at LEEG
        self.signal = factories.SignalFactory.create(status__state=workflow.LEEG)

    @mock.patch('signals.apps.signals.managers.update_status', autospec=True)
    def test_reopen_example_happy_flow(self, patched_udate_status_signal):
        self.assertEqual(self.signal.status.state, workflow.LEEG)

        # The workflow we want to check
        for new_state in HAPPY_REOPEN_SCENARIO:
            new_status_data = {'state': new_state, 'text': 'Dit is een test.'}
            Signal.actions.update_status(new_status_data, self.signal)

        self.assertEqual(self.signal.status.state, HAPPY_REOPEN_SCENARIO[-1])
        self.assertEqual(patched_udate_status_signal.send.call_count, 8)
        self.assertEqual(Status.objects.filter(state=workflow.HEROPEND).count(), 2)

    @mock.patch('signals.apps.signals.managers.update_status', autospec=True)
    def test_reopen_example_fails(self, patched_udate_status_signal):
        self.assertEqual(self.signal.status.state, workflow.LEEG)

        with self.assertRaises(ValidationError):
            for new_state in UNHAPPY_REOPEN_SCENARIO:
                new_status_data = {'state': new_state, 'text': 'Dit is een test.'}
                Signal.actions.update_status(new_status_data, self.signal)

        self.assertEqual(self.signal.status.state, workflow.BEHANDELING)
        self.assertEqual(patched_udate_status_signal.send.call_count, 4)
        self.assertEqual(Status.objects.filter(state=workflow.HEROPEND).count(), 0)
