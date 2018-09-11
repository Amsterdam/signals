import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from signals.apps.sigmax.handler import _generate_creeer_zaak_lk01_message, _send_stuf_message
from signals.apps.signals.models import Signal
from tests.apps.signals.factories import SignalFactory


def _get_test_signal():
    """
    Load a test signal from our fixture data.
    """
    fixture_file = os.path.join(
        settings.FIXTURES_DIR, 'datasets', 'internal', 'auth_signal.json')

    with open(fixture_file, 'r') as f:
        data = json.load(f)

    return data['results'][0]


# Known to still be problematic, work in progress
class Command(BaseCommand):
    help = 'Send a message to "Sigmax" as a manual test.'

    def handle(self, *args, **options):
        self.stdout.write('Send a message to Sigmax.')
        test_signal: Signal = SignalFactory.create()

        msg = _generate_creeer_zaak_lk01_message(test_signal)
        self.stdout.write('Hier het bericht:')
        self.stdout.write(msg)
        self.stdout.write('Einde bericht')

        self.stdout.write('Sending a message to Sigmax.')
        r = _send_stuf_message(msg)
        self.stdout.write('response status code: {}'.format(r.status_code))
        self.stdout.write('Logging response.text :')
        self.stdout.write(r.text)
