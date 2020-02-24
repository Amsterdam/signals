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
    workflow.BEHANDELING,
    workflow.INGEPLAND,
    workflow.GEANNULEERD,
    workflow.HEROPEND,
    workflow.AFGEHANDELD,
]

UNHAPPY_REOPEN_SCENARIO = [
    workflow.GEMELD,
    workflow.BEHANDELING,
    workflow.INGEPLAND,
    workflow.BEHANDELING,
    workflow.HEROPEND,
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

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.status.state, HAPPY_REOPEN_SCENARIO[-1])
        self.assertEqual(patched_udate_status_signal.send_robust.call_count, 9)
        self.assertEqual(Status.objects.filter(state=workflow.HEROPEND).count(), 2)

    @mock.patch('signals.apps.signals.managers.update_status', autospec=True)
    def test_reopen_example_fails(self, patched_udate_status_signal):
        self.assertEqual(self.signal.status.state, workflow.LEEG)

        with self.assertRaises(ValidationError):
            for new_state in UNHAPPY_REOPEN_SCENARIO:
                new_status_data = {'state': new_state, 'text': 'Dit is een test.'}
                Signal.actions.update_status(new_status_data, self.signal)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.status.state, workflow.BEHANDELING)
        self.assertEqual(patched_udate_status_signal.send_robust.call_count, 4)
        self.assertEqual(Status.objects.filter(state=workflow.HEROPEND).count(), 0)


class TestTransistion(TransactionTestCase):
    @mock.patch('signals.apps.signals.managers.update_status', autospec=True)
    def test_to_allowed_states(self, patched_update_status_signal):
        """
        Checks if a signal in a state can reach all allowed states that are configured in the
        workflow.ALLOWED_STATUS_CHANGES

        :param patched_update_status_signal:
        :return:
        """
        call_counter = 0

        for current_state in workflow.ALLOWED_STATUS_CHANGES:
            allowed_states = workflow.ALLOWED_STATUS_CHANGES[current_state]
            for allowed_state in allowed_states:
                signal = factories.SignalFactory.create(status__state=current_state)

                new_status_data = {'state': allowed_state,
                                   'text': 'Dit is een test.'}

                if allowed_state == workflow.TE_VERZENDEN:
                    new_status_data.update({'target_api': Status.TARGET_API_SIGMAX})

                Signal.actions.update_status(new_status_data, signal)
                signal.refresh_from_db()

                self.assertEqual(signal.status.state, allowed_state)

                call_counter += 1

        self.assertEqual(patched_update_status_signal.send_robust.call_count, call_counter)

    @mock.patch('signals.apps.signals.managers.update_status', autospec=True)
    def test_not_allowed_states(self, patched_update_status_signal):
        """
        Checks if a signal in a state can NOT reach all not allowed states. Calculated from the
        configured workflow.ALLOWED_STATUS_CHANGES

        :param patched_update_status_signal:
        :return:
        """
        all_states = workflow.ALLOWED_STATUS_CHANGES.keys()
        status_choices_dict = dict(workflow.STATUS_CHOICES)

        for current_state in workflow.ALLOWED_STATUS_CHANGES:
            allowed_states = workflow.ALLOWED_STATUS_CHANGES[current_state]
            not_allowed_states = all_states - allowed_states
            for not_allowed_state in not_allowed_states:
                with self.assertRaises(ValidationError) as ve:
                    signal = factories.SignalFactory.create(status__state=current_state)

                    new_status_data = {'state': not_allowed_state,
                                       'text': 'Dit is een test.'}

                    if not_allowed_state == workflow.TE_VERZENDEN:
                        new_status_data.update({'target_api': Status.TARGET_API_SIGMAX})

                    Signal.actions.update_status(new_status_data, signal)

                msg = 'Invalid state transition from `{}` to `{}`.'.format(
                    signal.status.get_state_display(),
                    status_choices_dict[not_allowed_state] if not_allowed_state else ''
                )

                self.assertEqual(ve.exception.messages[0], msg)
                self.assertEqual(signal.status.state, current_state)

        self.assertEqual(patched_update_status_signal.send_robust.call_count, 0)
