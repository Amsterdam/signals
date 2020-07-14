from unittest import mock

from django.core import mail
from django.test import TestCase

from signals.apps.signals import workflow
from signals.apps.signals.managers import create_initial, update_status
from tests.apps.signals.factories import SignalFactory, StatusFactory


class TestSignalReceivers(TestCase):
    signal = None

    def setUp(self):
        self.signal = SignalFactory.create()

    @mock.patch('signals.apps.email_integrations.reporter.signal_receivers.tasks', autospec=True)
    def test_create_initial_handler(self, mocked_tasks):
        create_initial.send_robust(sender=self.__class__, signal_obj=self.signal)
        mocked_tasks.send_mail_reporter_created.delay.assert_called_once_with(pk=self.signal.id)

    @mock.patch('signals.apps.email_integrations.reporter.signal_receivers.tasks', autospec=True)
    def test_update_status_handler(self, mocked_tasks):
        prev_status = self.signal.status
        new_status = StatusFactory.create(_signal=self.signal)

        self.signal.status = new_status
        self.signal.save()

        update_status.send_robust(sender=self.__class__,
                                  signal_obj=self.signal,
                                  status=new_status,
                                  prev_status=prev_status)

        mocked_tasks.send_mail_reporter_status_changed_afgehandeld.delay.assert_called_once_with(
            signal_pk=self.signal.id, status_pk=new_status.id, prev_status_pk=prev_status.pk
        )
        mocked_tasks.send_mail_reporter_status_changed_heropend.delay.assert_called_once_with(
            signal_pk=self.signal.pk, status_pk=new_status.id, prev_status_pk=prev_status.pk
        )
        mocked_tasks.send_mail_reporter_status_changed_ingepland.delay.assert_called_once_with(
            signal_pk=self.signal.pk, status_pk=new_status.id, prev_status_pk=prev_status.pk
        )
        mocked_tasks.send_mail_reporter_status_changed_split.delay.assert_called_once_with(
            signal_pk=self.signal.pk, status_pk=new_status.id, prev_status_pk=prev_status.pk
        )

    def test_send_only_one_enail(self):
        # Check that old behavior is maintained after MailActions refactor and
        # before the new mail rules are implemented. We want only one mail to be
        # sent upon a status update to AFGEHANDELD.
        prev_status = self.signal.status
        new_status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)

        self.signal.status = new_status
        self.signal.save()

        update_status.send_robust(sender=self.__class__,
                                  signal_obj=self.signal,
                                  status=new_status,
                                  prev_status=prev_status)

        self.assertEqual(len(mail.outbox), 1)
