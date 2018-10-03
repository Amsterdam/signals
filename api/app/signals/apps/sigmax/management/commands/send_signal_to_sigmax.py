from django.core.management.base import BaseCommand

from signals.apps.signals import workflow
from signals.apps.signals.models import Signal, Status
from tests.apps.signals.factories import SignalFactoryValidLocation


class Command(BaseCommand):
    help = 'Send a message to "Sigmax" as a manual test WITH Celery.'

    def handle(self, *args, **options):
        self.stdout.write('Creating a melding in SIA')
        test_signal = SignalFactoryValidLocation.create(
            text='Dit is een test bericht van Datapunt Amsterdam aan Sigmax City Control',
        )

        self.stdout.write('Updating status to \'TE_VERZENDEN\' with target API \'sigmax\'')
        Signal.actions.update_status({
            'state': workflow.TE_VERZENDEN,
            'target_api': Status.TARGET_API_SIGMAX,
            'text': 'klaar om naar Sigmax/CityControl te versturen',
        }, signal=test_signal)

        self.stdout.write('Status should now be set, and signal should be sent.')
