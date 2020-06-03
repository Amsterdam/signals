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

    def handle(self, *args, **options):
        data_loaders = self._get_data_loaders()

        self.stdout.write('The following AreaTypes can be loaded:')
        self.stdout.write(repr(list(data_loaders.keys())))
