from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TransactionTestCase


class TestCommand(TransactionTestCase):
    @patch('signals.apps.reporting.csv.datawarehouse.save_csv_files_datawarehouse')
    def test_command(self, patched_save_csv_files_datawarehouse):
        out = StringIO()
        err = StringIO()

        call_command('dumpcsv', stdout=out, stderr=err)

        self.assertEqual(out.getvalue(), '')
        self.assertEqual(err.getvalue(), '')

        patched_save_csv_files_datawarehouse.assert_called_once()
