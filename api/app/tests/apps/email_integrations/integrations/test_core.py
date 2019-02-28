from datetime import datetime

from django.core import mail
from django.test import TestCase

from signals.apps.email_integrations.integrations import core
from signals.apps.signals import workflow
from tests.apps.signals.factories import SignalFactory, StatusFactory


class TestCore(TestCase):

    def setUp(self):
        self.signal = SignalFactory.create(reporter__email='foo@bar.com')
        self.signal.incident_date_start = datetime(2018, 10, 10, 12, 0, 0)
        self.signal_no_email = SignalFactory.create(reporter__email='')

    def test_send_mail_reporter_created(self):
        num_of_messages = core.send_mail_reporter_created(self.signal)

        self.assertEqual(num_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Bedankt voor uw melding ({self.signal.id})')
        self.assertEqual(mail.outbox[0].to, ['foo@bar.com', ])

        self.assertIn('10 oktober 2018 12:00', mail.outbox[0].body)

    def test_send_mail_reporter_created_no_email(self):
        num_of_messages = core.send_mail_reporter_created(self.signal_no_email)

        self.assertEqual(num_of_messages, None)

    def test_create_initial_create_notification_message(self):
        message = core.create_initial_create_notification_message(self.signal)

        self.assertIn(str(self.signal.id), message)
        self.assertIn(self.signal.text, message)
        self.assertIn(self.signal.reporter.email, message)

    def test_send_mail_reporter_status_changed_afgehandeld(self):
        # Prepare signal with status change to `AFGEHANDELD`.
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.status.save()

        num_of_messages = core.send_mail_reporter_status_changed_afgehandeld(self.signal, status)

        self.assertEqual(num_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Betreft melding: {self.signal.id}')
        self.assertEqual(mail.outbox[0].to, ['foo@bar.com', ])

    def test_send_mail_reporter_status_changed_afgehandeld_no_status_afgehandeld(self):
        num_of_messages = core.send_mail_reporter_status_changed_afgehandeld(self.signal,
                                                                             self.signal.status)

        self.assertEqual(num_of_messages, None)

    def test_send_mail_reporter_status_changed_afgehandeld_no_email(self):
        # Prepare signal with status change to `AFGEHANDELD`.
        status = StatusFactory.create(_signal=self.signal_no_email, state=workflow.AFGEHANDELD)
        self.signal_no_email.status = status
        self.signal_no_email.status.save()

        num_of_messages = core.send_mail_reporter_status_changed_afgehandeld(self.signal_no_email,
                                                                             status)

        self.assertEqual(num_of_messages, None)

    def test_create_status_change_notification_message(self):
        # Prepare signal with status change to `AFGEHANDELD`.
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD, text='Done.')
        self.signal.status = status
        self.signal.status.save()

        message = core.create_status_change_notification_message(self.signal, self.signal.status)

        self.assertIn(str(self.signal.id), message)
        self.assertIn(self.signal.text, message)
        self.assertIn(self.signal.status.text, message)

    def test_send_mail_reporter_status_changed_afgehandeld_txt_and_html(self):
        mail.outbox = []

        # Prepare signal with status change to `AFGEHANDELD`.
        status = StatusFactory.create(_signal=self.signal, state=workflow.AFGEHANDELD)
        self.signal.status = status
        self.signal.status.save()

        num_of_messages = core.send_mail_reporter_status_changed_afgehandeld(self.signal, status)

        self.assertEqual(num_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        self.assertEqual(message.subject, f'Betreft melding: {self.signal.id}')
        self.assertEqual(message.to, ['foo@bar.com', ])

        txt_message = core.create_status_change_notification_message(signal=self.signal,
                                                                     status=status)
        self.assertEqual(message.body, txt_message)

        content, mime_type = message.alternatives[0]
        html_message = core.create_status_change_notification_html_message(signal=self.signal,
                                                                           status=status)
        self.assertEqual(mime_type, 'text/html')
        self.assertEqual(content, html_message)


class TestSignalSplitEmailFlow(TestCase):
    def setUp(self):
        self.parent_signal = SignalFactory.create(
            status__state=workflow.GESPLITST, parent=None, reporter__email='piet@example.com')
        self.child_signal_1 = SignalFactory.create(
            status__state=workflow.GEMELD, parent=self.parent_signal)
        self.child_signal_2 = SignalFactory.create(
            status__state=workflow.GEMELD, parent=self.parent_signal)

    def test_send_mail_reporter_status_changed_split_faal(self):
        num_of_messages = core.send_mail_reporter_status_changed_split(
            self.parent_signal, self.parent_signal.status)

        self.assertEqual(num_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Betreft melding: {self.parent_signal.id}')
        self.assertEqual(mail.outbox[0].to, ['piet@example.com'])

    def test_send_mail_reporter_status_changed_split_no_correct_status(self):
        wrong_status = StatusFactory.create(state=workflow.GEMELD)
        self.parent_signal.status = wrong_status

        num_of_messages = core.send_mail_reporter_status_changed_split(
            self.parent_signal, self.parent_signal.status)
        self.assertEqual(num_of_messages, None)

    def test_send_mail_reporter_status_changed_split_no_email(self):
        self.parent_signal.reporter.email = None
        self.parent_signal.save()

        num_of_messages = core.send_mail_reporter_status_changed_split(
            self.parent_signal, self.parent_signal.status)
        self.assertEqual(num_of_messages, None)

    def test_create_status_change_notification_split(self):

        txt_message = core.create_status_change_notification_split(
            self.parent_signal, self.parent_signal.status)

        for signal in [self.parent_signal, self.child_signal_1, self.child_signal_2]:
            self.assertIn(str(signal.id), txt_message)
