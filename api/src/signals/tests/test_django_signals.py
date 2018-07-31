from unittest import mock

from django.test import testcases

from signals.tests.factories import SignalFactory


class TestDjangoSignals(testcases.TestCase):

    @mock.patch('signals.django_signals.tasks')
    def test_post_save_signal_created(self, mocked_tasks):
        signal = SignalFactory.create()
        mocked_tasks.push_to_sigmax.delay.assert_called_once_with(id=signal.id)
        mocked_tasks.email_to_apptimize.delay.assert_called_once_with(
            id=signal.id)

    def test_post_save_signal_updated(self):
        signal = SignalFactory.create()
        signal.text = 'Signal is updated'

        with mock.patch('signals.django_signals.tasks') as mocked_tasks:
            signal.save()
            mocked_tasks.push_to_sigmax.delay.assert_not_called()
            mocked_tasks.email_to_apptimize.delay.assert_called_once_with(
                id=signal.id)
