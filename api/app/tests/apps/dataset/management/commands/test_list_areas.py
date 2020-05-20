from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from signals.apps.dataset.base import AreaLoader
from signals.apps.dataset.management.commands.list_areas import Command


class FakeAreaLoaderA(AreaLoader):
    PROVIDES = ['fake-a']


class FakeAreaLoaderB(AreaLoader):
    PROVIDES = ['fake-b']


class TestListAreas(TestCase):
    @patch(
        'signals.apps.dataset.management.commands.list_areas.inspect.getmembers',
        return_value=[
            (FakeAreaLoaderA.__name__, FakeAreaLoaderA),
            (FakeAreaLoaderB.__name__, FakeAreaLoaderB),
        ]
    )
    def test_get_data_loaders(self, patched_getmembers):
        cmd = Command()
        data_loaders = cmd._get_data_loaders()

        self.assertEqual(len(data_loaders), 2)
        self.assertEqual(set(data_loaders), set(['fake-a', 'fake-b']))
        self.assertEqual(data_loaders['fake-a'], FakeAreaLoaderA)
        self.assertEqual(data_loaders['fake-b'], FakeAreaLoaderB)

    @patch(
        'signals.apps.dataset.management.commands.list_areas.inspect.getmembers',
        return_value=[
            (FakeAreaLoaderA.__name__, FakeAreaLoaderA),
            (FakeAreaLoaderB.__name__, FakeAreaLoaderB),
        ]
    )
    def test_list_areas_command(self, patched_getmembers):
        buffer = StringIO()
        call_command('list_areas', stdout=buffer)

        output = buffer.getvalue()
        self.assertIn('fake-a', output)
        self.assertIn('fake-b', output)
