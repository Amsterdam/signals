from django.core.management import BaseCommand

from signals.apps.dataset.sources.amsterdamse_bos import load_amsterdamse_bos


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Loading Amsterdamse Bos Geometry ...')
        load_amsterdamse_bos()
        self.stdout.write('... done.')
