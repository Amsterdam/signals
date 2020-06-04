from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from signals.apps.dataset.base import AreaLoader


class FakeAreaLoader(AreaLoader):
    PROVIDES = ['fake']

    def __init__(self, type_string, directory=None):
        pass

    def load(self):
        pass


class TestLoadAreas(TestCase):
    @patch(
        'signals.apps.dataset.management.commands.load_areas.inspect.getmembers',
        return_value=[
            (FakeAreaLoader.__name__, FakeAreaLoader),
        ]
    )
    def test_load_areas(self, patched_getmembers):
        buffer = StringIO()
        call_command('load_areas', 'fake', stdout=buffer)

        output = buffer.getvalue()
        self.assertIn('Loading "fake" areas ...', output)
