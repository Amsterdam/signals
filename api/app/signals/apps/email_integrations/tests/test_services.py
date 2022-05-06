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
                                     title='Uw melding {{ signal_id }}',
                                     body='{{ text }} {{ created_at }} {{ handling_message }} {{ ORGANIZATION_NAME }}')

    def test_send_email(self):
        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')
        self.assertTrue(MailService.mail(signal))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.id}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
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

        self.assertTrue(MailService.mail(signal))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Meer over uw melding {signal.id}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(Note.objects.count(), 1)


class TestMailActionsSpecialCasesActions(TestCase):
    def test_send_email_no_actions(self):
        MailService.actions = ()

        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')
        self.assertFalse(MailService.mail(signal.pk))
        self.assertEqual(len(mail.outbox), 0)

    def test_send_email_lambda_actions(self):
        MailService.actions = (lambda x, dry_run: False, lambda x, dry_run: False, lambda x, dry_run: False,
                               lambda x, dry_run: False)

        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')
        self.assertFalse(MailService.mail(signal.pk))
        self.assertEqual(len(mail.outbox), 0)
