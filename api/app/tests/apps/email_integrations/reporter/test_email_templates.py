import uuid

from django.core import mail
from django.test import TestCase

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.reporter.mail_actions import SIGNAL_MAIL_RULES, MailActions
from signals.apps.signals.factories import SignalFactory


class TestEmailTemplates(TestCase):
    def setUp(self):
        def get_email():
            return f'{uuid.uuid4()}@example.com'

        self.email_template = EmailTemplate.objects.create(
            key=EmailTemplate.SIGNAL_CREATED,
            title='Template title {{ signal.id }}',
            body='# Template title\n Thanks a lot for reporting **{{ signal.id }}**',
        )

        self.signal = SignalFactory.create(reporter__email=get_email())

    def test_email_template(self):
        ma = MailActions(mail_rules=SIGNAL_MAIL_RULES)
        ma.apply(signal_id=self.signal.id)

        self.assertEqual(f'Template title {self.signal.id}', mail.outbox[0].subject)
        self.assertEqual(f'Template title\n\nThanks a lot for reporting {self.signal.id}\n\n', mail.outbox[0].body)

        body, mime_type = mail.outbox[0].alternatives[0]
        self.assertEqual(mime_type, 'text/html')
        self.assertIn('<h1>Template title</h1>', body)
        self.assertIn(f'<p>Thanks a lot for reporting <strong>{self.signal.id}</strong></p>', body)
