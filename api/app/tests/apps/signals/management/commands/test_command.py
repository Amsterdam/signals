from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TransactionTestCase


class TestCommand(TransactionTestCase):
    @patch('signals.utils.remove_old_reporters.remove_old_reporters')
    def test_command(self, patched_remove_old_reporters):
        out = StringIO()
        err = StringIO()

        call_command('remove_old_reporters', stdout=out, stderr=err)
        patched_remove_old_reporters.assert_called_once()
