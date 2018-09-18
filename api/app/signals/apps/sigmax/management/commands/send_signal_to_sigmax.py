import json
import os
import random

from django.conf import settings
from django.core.management.base import BaseCommand

from signals.apps.sigmax.handler import (
    _generate_creeer_zaak_lk01_message,
    _send_stuf_message,
    CREEER_ZAAK_SOAPACTION,
    VOEG_ZAAKDOCUMENT_TOE_SOAPACTION,
)
from signals.apps.signals.models import Signal
from tests.apps.signals.factories import (
    SignalFactoryValidLocation, VALID_LOCATIONS)


# Known to still be problematic, work in progress
class Command(BaseCommand):
    help = 'Send a message to "Sigmax" as a manual test.'

    def handle(self, *args, **options):
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
