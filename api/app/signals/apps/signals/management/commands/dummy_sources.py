from django.core.management import BaseCommand
from django.utils.text import slugify
from faker import Faker

from signals.apps.signals.factories import SourceFactory

fake = Faker()


class Command(BaseCommand):
    default_to_create = 1
    min_to_create = 1
    max_to_create = 10

    def add_arguments(self, parser):
        parser.add_argument('--to-create', type=int, help=f'Total random Sources to create (max {self.max_to_create}). '
                                                          f'Default {self.default_to_create}.')

    def handle(self, *args, **options):
        to_create = int(options['to_create'] or self.default_to_create)
        if not self.min_to_create <= to_create <= self.max_to_create:
            self.stderr.write(f'The to create option must be an integer from {self.min_to_create} to '
                              f'{self.max_to_create}, {to_create} given')
        else:
            for _ in range(to_create):
                SourceFactory.create(name=slugify(fake.words()), description=fake.sentence(nb_words=10))
            self.stdout.write(f'Created {to_create} random Source(s)')
