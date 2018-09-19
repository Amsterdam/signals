from django.core.management.base import BaseCommand

from signals.apps.sigmax.handler import (
    CREEER_ZAAK_SOAPACTION,
    VOEG_ZAAKDOCUMENT_TOE_SOAPACTION,
    _generate_creeer_zaak_lk01_message,
    _generate_voeg_zaak_document_toe_lk01,
    _send_stuf_message
)
from signals.apps.signals.models import Signal
from tests.apps.signals.factories import SignalFactoryValidLocation


# Known to still be problematic, work in progress
class Command(BaseCommand):
    help = 'Send a message to "Sigmax" as a manual test.'

    def handle(self, *args, **options):
        # first step; generate a "Zaak" in Sigmax's system
        self.stdout.write('Send a message to Sigmax.')
        test_signal: Signal = SignalFactoryValidLocation.create(
            text='Dit is een test bericht van Datapunt Amsterdam aan Sigmax City Control',
        )

        msg = _generate_creeer_zaak_lk01_message(test_signal)
        self.stdout.write('Hier het bericht:')
        self.stdout.write(msg)
        self.stdout.write('Einde bericht')

        self.stdout.write('Sending a message to Sigmax.')
        r = _send_stuf_message(msg, CREEER_ZAAK_SOAPACTION)
        self.stdout.write('response status code: {}'.format(r.status_code))
        self.stdout.write('Logging response.text :')
        self.stdout.write(r.text)

        # second step; generate PDF and send it to SIGMAX
        msg_2 = _generate_voeg_zaak_document_toe_lk01(test_signal)

        self.stdout.write('Sending a PDF to Sigmax.')
        r = _send_stuf_message(msg_2, VOEG_ZAAKDOCUMENT_TOE_SOAPACTION)
        self.stdout.write('response status code: {}'.format(r.status_code))
        self.stdout.write('Logging response.text :')
        self.stdout.write(r.text)
