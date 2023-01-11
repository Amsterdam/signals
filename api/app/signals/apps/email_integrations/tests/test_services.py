# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from django.conf import settings
from django.core import mail
from django.test import TestCase

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.services import MailService
from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory
from signals.apps.signals.models import Note


class TestMailActions(TestCase):
    def setUp(self):
        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_CREATED,
                                     title='Uw melding {{ formatted_signal_id }}',
                                     body='{{ text }} {{ created_at }} {{ handling_message }} {{ ORGANIZATION_NAME }}')

    def test_send_status_email(self):
        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')
        self.assertTrue(MailService.status_mail(signal))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.get_id_display()}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(Note.objects.count(), 1)

    def test_send_system_mail_feedback_received(self):
        """
        Test the sending of the sending mail from the mail services
        """
        EmailTemplate.objects.create(
            key=EmailTemplate.SIGNAL_FEEDBACK_RECEIVED,
            title='Uw Feedback is ontvangen',
            body='test text {{ feedback_text }} {{ feedback_text_extra }}'
        )
        signal = SignalFactory.create(status__state=workflow.GEMELD,
                                      reporter__email='test@example.com')

        text = 'my text _1234567'
        text_extra = 'my extra text _extra_987654321'
        feedback = FeedbackFactory.create(
            _signal=signal,
            text=text,
            text_extra=text_extra,
        )
        result = MailService.system_mail(
            signal=signal, action_name='feedback_received', feedback=feedback)

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn(text, mail.outbox[0].body)
        self.assertIn(text_extra, mail.outbox[0].body)
        self.assertEqual(Note.objects.count(), 1)

    def test_only_send_feedback_negative_contact_mail(self):
        """
        Test to see if when a status is changed from VERZOEK_TOT_AFHANDELING to AFGEHANDELD and has allows_contact on
        the feedback to only send one email
        """
        self.assertEqual(len(mail.outbox), 0)
        signal = SignalFactory.create(status__state=workflow.VERZOEK_TOT_AFHANDELING,
                                      reporter__email='test@example.com')
        status = StatusFactory.create(_signal=signal, state=workflow.AFGEHANDELD)
        feedback = FeedbackFactory.create(
            allows_contact=True,
            _signal=signal,
        )
        feedback.save()
        signal.status = status  # change to new status AFGEHANDELD
        signal.save()

        self.assertTrue(MailService.status_mail(signal))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Meer over uw melding {signal.get_id_display()}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(Note.objects.count(), 1)
