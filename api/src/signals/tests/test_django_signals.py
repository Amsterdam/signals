from unittest import mock

from django.test import testcases

from signals.tests.factories import SignalFactory


class TestDjangoSignals(testcases.TestCase):

    @mock.patch('signals.django_signals.tasks')
    def test_post_save_signal_created(self, mocked_tasks):
        signal = SignalFactory.build()
        signal.location.save()
        signal.status.save()
        signal.reporter.save()
        signal.category.save()
        signal.save()  # Triggers Django `post_save` signal.

        mocked_tasks.push_to_sigmax.delay.assert_called_once_with(id=signal.id)
        mocked_tasks.send_mail_apptimize.delay.assert_called_once_with(
            id=signal.id)
        mocked_tasks.send_mail_flex_horeca.delay.assert_called_once_with(
            id=signal.id)

    @mock.patch('signals.django_signals.tasks')
    def test_post_save_signal_updated(self, mocked_tasks):
        signal = SignalFactory.create()

        signal.text = 'Signal is updated'
        signal.save()
        mocked_tasks.push_to_sigmax.delay.assert_not_called()
        mocked_tasks.send_mail_apptimize.delay.assert_called_once_with(
            id=signal.id)
        mocked_tasks.send_mail_flex_horeca.delay.assert_called_once_with(
            id=signal.id)
