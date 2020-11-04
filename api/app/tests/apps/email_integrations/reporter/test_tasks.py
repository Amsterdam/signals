from unittest import mock

from django.test import TestCase

from signals.apps.email_integrations.reporter import tasks
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory
from signals.apps.signals.models import Signal, Status


class TestTasks(TestCase):
    signal = None

    def setUp(self):
        self.signal = SignalFactory.create()
        self.prev_status = self.signal.status
        self.signal.status = StatusFactory(_signal=self.signal, state=workflow.BEHANDELING)
        self.signal.save()

    @mock.patch('signals.apps.email_integrations.reporter.tasks.mail', autospec=True)
    def test_send_mail_reporter_created(self, mocked_mail):
        tasks.send_mail_reporter_created(pk=self.signal.id)
        mocked_mail.send_mail_reporter_created.assert_called_once_with(self.signal)

    @mock.patch('signals.apps.email_integrations.reporter.tasks.mail', autospec=True)
    def test_send_mail_reporter_created_signal_not_found(self, mocked_mail):
        with self.assertRaises(Signal.DoesNotExist):
            tasks.send_mail_reporter_created(pk=999)
        mocked_mail.send_mail_reporter_created.assert_not_called()

    @mock.patch('signals.apps.email_integrations.reporter.tasks.mail', autospec=True)
    def test_send_mail_reporter_status_changed(self, mocked_mail):
        tasks.send_mail_reporter_status_changed(signal_pk=self.signal.id,
                                                status_pk=self.signal.status.id,
                                                prev_status_pk=self.prev_status.id)
        mocked_mail.send_mail_reporter_status_changed.assert_called_once_with(
            self.signal, self.signal.status, self.prev_status
        )

    @mock.patch('signals.apps.email_integrations.reporter.tasks.mail', autospec=True)
    def test_send_mail_reporter_status_changed_status_not_found(self, mocked_mail):
        with self.assertRaises(Status.DoesNotExist):
            tasks.send_mail_reporter_status_changed(
                signal_pk=self.signal.pk, status_pk=999, prev_status_pk=self.prev_status.id
            )
        mocked_mail.send_mail_reporter_status_changed.assert_not_called()
