from django.core.management import BaseCommand

from signals.apps.dataset.sources.gebieden import APIGebiedenLoader


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('type_string', type=str, help='stadsdeel, wijk or buurt')

    def handle(self, *args, **options):
        assert 'type_string' in options
        loader = APIGebiedenLoader(options['type_string'])

        self.stdout.write(f'Loading {options["type_string"]} areas from gebieden API...')
        loader.load()
        self.stdout.write('...done.')
