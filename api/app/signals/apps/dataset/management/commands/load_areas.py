import inspect

from django.core.management import BaseCommand

from signals.apps.dataset import sources
from signals.apps.dataset.base import AreaLoader


class Command(BaseCommand):
    def _get_data_loaders(self):
        """
        Get mapping of DataLoader name to DataLoader class for all sources.
        """
        data_loaders = {}
        for name, item in inspect.getmembers(sources):
            if inspect.isclass(item) and issubclass(item, AreaLoader):
                for key in item.PROVIDES:
                    data_loaders[key] = item

        return data_loaders

    def add_arguments(self, parser):
        parser.add_argument('type_string', type=str, help='stadsdeel, wijk or buurt')

    def handle(self, *args, **options):
        data_loaders = self._get_data_loaders()

        type_string = options['type_string']
        assert type_string in data_loaders

        loader = data_loaders[type_string](type_string)

        self.stdout.write(f'Loading {type_string} areas from gebieden API...')
        loader.load()
        self.stdout.write('...done.')
