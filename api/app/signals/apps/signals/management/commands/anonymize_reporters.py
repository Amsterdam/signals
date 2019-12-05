from django.core.management import BaseCommand

from signals.apps.signals.tasks import anonymize_reporters


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, help='')

    def handle(self, *args, **options):
        days = options['days'] or 365
        if days < 365:
            self.stderr.write('days should be 365 or higher')
        else:
            reporter_count = anonymize_reporters(days=days)
            self.stdout.write('Anonymized {} reporter(s)'.format(reporter_count))
