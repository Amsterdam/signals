from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TransactionTestCase


class TestCommand(TransactionTestCase):
    @patch('signals.apps.signals.tasks.anonymize_reporters')
    def test_command(self, patched_anonymize_reporters):
        out = StringIO()
        err = StringIO()

        call_command('anonymize_reporters', stdout=out, stderr=err)
        patched_anonymize_reporters.assert_called_once()

    @patch('signals.apps.signals.tasks.anonymize_reporters')
    def test_command_invalid_days(self, patched_anonymize_reporters):
        out = StringIO()
        err = StringIO()

        call_command('anonymize_reporters', days=1, stdout=out, stderr=err)
        patched_anonymize_reporters.assert_not_called()
