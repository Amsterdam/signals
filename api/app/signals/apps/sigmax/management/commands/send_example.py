from django.core.management.base import BaseCommand

# Known to still be problematic, work in progress
from signals.apps.sigmax.send_example import send_example


class Command(BaseCommand):
    help = 'Send a message to "Sigmax" as a manual test.'

    def add_arguments(self, parser):
        parser.add_argument(
            'example', nargs='?', help='Which message to send 1-4', default=1)
        parser.add_argument(
            '--zkn_uuid', nargs='?', help='Zaak UUID to use', default='')
        parser.add_argument(
            '--doc_uuid', nargs='?', help='Document UUID to use', default='')

    def handle(self, *args, **options):
        self.stdout.write('Sending a message to Sigmax.')
        self.stdout.write(str(options))
        r = send_example(**options)
        self.stdout.write('response status code: {}'.format(r.status_code))
        self.stdout.write('Logging response.text :')
        self.stdout.write(r.text)
