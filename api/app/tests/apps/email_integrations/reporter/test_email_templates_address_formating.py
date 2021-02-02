from django.core import mail
from django.test import TestCase

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.reporter.mail_actions import SIGNAL_MAIL_RULES, MailActions
from signals.apps.signals.factories import SignalFactoryValidLocation


class TestEmailTemplateAddressFormatting(TestCase):

    def test_address_formatting(self):
        EmailTemplate.objects.create(
            key=EmailTemplate.SIGNAL_CREATED,
            title='Template title {{ signal.id }}',
            body='{{ signal.location|format_address:"O hl, P W" }}',
        )

        signal = SignalFactoryValidLocation.create(reporter__email='test@example.com')

        ma = MailActions(mail_rules=SIGNAL_MAIL_RULES)
        ma.apply(signal_id=signal.id)

        self.assertEqual(f'Template title {signal.id}', mail.outbox[0].subject)

        postcode_no_spaces = signal.location.address["postcode"].replace(' ', '')
        postcode = f'{postcode_no_spaces[:4]} {postcode_no_spaces[-2:]}'

        if 'huisletter' not in signal.location.address or len(signal.location.address['huisletter'].strip()) == 0:
            expected_address = f'{signal.location.address["openbare_ruimte"]} ' \
                               f'{signal.location.address["huisnummer"]}, ' \
                               f'{postcode} {signal.location.address["woonplaats"]}\n\n'
        else:
            expected_address = f'{signal.location.address["openbare_ruimte"]} ' \
                               f'{signal.location.address["huisnummer"]}{signal.location.address["huisletter"]}, ' \
                               f'{postcode} {signal.location.address["woonplaats"]}\n\n'
        self.assertEqual(expected_address, mail.outbox[0].body)
