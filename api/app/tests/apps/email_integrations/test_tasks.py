from unittest import mock

from django.test import TestCase

from signals.apps.email_integrations import tasks
from signals.apps.signals.models import Signal, Status
from tests.apps.signals.factories import SignalFactory, StatusFactory


class TestTasks(TestCase):

    @mock.patch('signals.apps.email_integrations.tasks.default', autospec=True)
    def test_send_mail_reporter(self, mocked_default):
        signal = SignalFactory.create()

        tasks.send_mail_reporter(pk=signal.id)

        mocked_default.send_mail_reporter.assert_called_once_with(signal)

    @mock.patch('signals.apps.email_integrations.tasks.default', autospec=True)
    def test_send_mail_reporter_signal_not_found(self, mocked_default):
        with self.assertRaises(Signal.DoesNotExist):
            tasks.send_mail_reporter(pk=999)

        mocked_default.send_mail_reporter.assert_not_called()

    @mock.patch('signals.apps.email_integrations.tasks.default', autospec=True)
    def test_send_mail_status_change(self, mocked_default):
        signal = SignalFactory.create()
        prev_status = signal.status
        status = StatusFactory.create(_signal=signal)

        tasks.send_mail_status_change(status_pk=status.id, prev_status_pk=prev_status.id)

        mocked_default.send_mail_status_change.assert_called_once_with(status, prev_status)

    @mock.patch('signals.apps.email_integrations.tasks.default', autospec=True)
    def test_send_mail_status_change_status_not_found(self, mocked_default):
        with self.assertRaises(Status.DoesNotExist):
            tasks.send_mail_status_change(status_pk=999, prev_status_pk=888)

        mocked_default.send_mail_status_change.assert_not_called()

    @mock.patch('signals.apps.email_integrations.tasks.apptimize', autospec=True)
    def test_send_mail_apptimize(self, mocked_apptimize):
        signal = SignalFactory.create()

        tasks.send_mail_apptimize(pk=signal.id)

        mocked_apptimize.send_mail.assert_called_once_with(signal)

    @mock.patch('signals.apps.email_integrations.tasks.apptimize', autospec=True)
    def test_send_mail_apptimize_signal_not_found(self, mocked_apptimize):
        with self.assertRaises(Signal.DoesNotExist):
            tasks.send_mail_apptimize(pk=999)

        mocked_apptimize.send_mail.assert_not_called()

    @mock.patch('signals.apps.email_integrations.tasks.flex_horeca', autospec=True)
    def test_send_mail_flex_horeca(self, mocked_flex_horeca):
        signal = SignalFactory.create()

        tasks.send_mail_flex_horeca(pk=signal.id)

        mocked_flex_horeca.send_mail.assert_called_once_with(signal)

    @mock.patch('signals.apps.email_integrations.tasks.flex_horeca', autospec=True)
    def test_send_mail_flex_horeca_signal_not_found(self, mocked_flex_horeca):
        with self.assertRaises(Signal.DoesNotExist):
            tasks.send_mail_flex_horeca(pk=999)

        mocked_flex_horeca.send_mail.assert_not_called()

    @mock.patch('signals.apps.email_integrations.tasks.handhaving_or', autospec=True)
    def test_send_mail_handhaving_or(self, mocked_handhaving_or):
        signal = SignalFactory.create()

        tasks.send_mail_handhaving_or(pk=signal.id)

        mocked_handhaving_or.send_mail.assert_called_once_with(signal)

    @mock.patch('signals.apps.email_integrations.tasks.handhaving_or', autospec=True)
    def test_send_mail_handhaving_or_signal_not_found(self, mocked_handhaving_or):
        with self.assertRaises(Signal.DoesNotExist):
            tasks.send_mail_handhaving_or(pk=999)

        mocked_handhaving_or.send_mail.assert_not_called()
