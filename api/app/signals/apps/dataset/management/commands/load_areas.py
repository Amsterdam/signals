import inspect
import os
from tempfile import TemporaryDirectory

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
        parser.add_argument('type_string', type=str, help='Use list_areas command to see options.')
        parser.add_argument('--dir', type=str, default=None, help='Directory to use for data processing.')

    def handle(self, *args, **options):
        data_loaders = self._get_data_loaders()

        type_string = options['type_string']
        assert type_string in data_loaders
        self.stdout.write(f'Loading "{type_string}" areas ...')

        # If no directory is specified, create a temporary directory to do the
        # processing. It is possible to specify the processing directory so that
        # it may be a Docker tempfs mount (SIA is generally deployed in a Docker
        # container, we do not want to bloat it).
        if options['dir'] is None:
            with TemporaryDirectory() as directory:
                loader = data_loaders[type_string](type_string, directory)
                loader.load()
        else:
            assert os.path.exists(options['dir'])
            loader = data_loaders[type_string](type_string, options['dir'])
            loader.load()

        self.stdout.write('...done.')
