# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django.conf import settings
from django.core import mail
from django.test import TestCase

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.services import MailService
from signals.apps.signals.factories import SignalFactory


class TestEmailTemplates(TestCase):
    def setUp(self):
        self.email_template = EmailTemplate.objects.create(
            key=EmailTemplate.SIGNAL_CREATED,
            title='Template title {{ signal_id }}',
            body='# Template title\n Thanks a lot for reporting **{{ signal_id }}** '
                 '{{ text }}\n{{ ORGANIZATION_NAME }}',
        )

    def test_email_template(self):
        self.assertEqual(str(self.email_template), 'Template title {{ signal_id }}')

        signal = SignalFactory.create(reporter__email='test@example.com')

        MailService.mail(signal=signal)

        self.assertEqual(f'Template title {signal.id}', mail.outbox[0].subject)
        self.assertEqual(f'Template title\n\nThanks a lot for reporting {signal.id} {signal.text}\n'
                         f'{settings.ORGANIZATION_NAME}\n\n', mail.outbox[0].body)

        body, mime_type = mail.outbox[0].alternatives[0]
        self.assertEqual(mime_type, 'text/html')
        self.assertIn('<h1>Template title</h1>', body)
        self.assertIn(f'<p>Thanks a lot for reporting <strong>{signal.id}</strong>', body)

    def test_organization_name_contains_quote(self):
        signal = SignalFactory.create(reporter__email='test@example.com')

        with self.settings(ORGANIZATION_NAME='Gemeente \'s-Hertogenbosch'):
            MailService.mail(signal=signal)

        self.assertEqual(f'Template title {signal.id}', mail.outbox[0].subject)
        self.assertEqual(f'Template title\n\nThanks a lot for reporting {signal.id} {signal.text}\n'
                         f'Gemeente \'s-Hertogenbosch\n\n', mail.outbox[0].body)

    def test_evil_input(self):
        evil_signal = SignalFactory.create(reporter__email='test@example.com',
                                           text='<script>alert("something evil");</script>')

        MailService.mail(signal=evil_signal)

        self.assertEqual(f'Template title {evil_signal.id}', mail.outbox[0].subject)
        self.assertEqual(f'Template title\n\nThanks a lot for reporting {evil_signal.id} '
                         f'alert("something evil");\n{settings.ORGANIZATION_NAME}\n\n', mail.outbox[0].body)
