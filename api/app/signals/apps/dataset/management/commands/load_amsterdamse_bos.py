from django.core.management import BaseCommand

from signals.apps.dataset.sources.amsterdamse_bos import SIAStadsdeelLoader


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Loading Amsterdamse Bos Geometry ...')
        sl = SIAStadsdeelLoader('sia-stadsdeel')
        sl.load()
        self.stdout.write('... done.')
