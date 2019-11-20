import shlex
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase as DjangoTestCase

from signals.apps.reporting.management.commands.export_signals_csv import convert_categories
from tests.apps.reporting.models.test_export import SignalsExportTestDataMixin


class TestExportSignalsCSV(SignalsExportTestDataMixin, DjangoTestCase):
    def test_convert_categories_happy_flow(self):
        data = '[[A,a],[B,b]]'
        expected = [
            {'main_slug': 'A', 'sub_slug': 'a'},
            {'main_slug': 'B', 'sub_slug': 'b'},
        ]
        self.assertEqual(convert_categories(data), expected)

    @patch('signals.apps.reporting.management.commands.export_signals_csv.CSVExport', autospec=True)
    def test_daily_export_cli_handling(self, mocked_model):
        mocked_model.objects = MagicMock()
        cmd = 'export_signals_csv NAME --year 2019 --month 12 --day 31 --categories [[main,cat_a]]'
        call_command(*shlex.split(cmd))

        expected_export_parameters = {
            'year': 2019,
            'month': 12,
            'day': 31,
            'categories': [{'main_slug': 'main', 'sub_slug': 'cat_a'}]
        }

        mocked_model.objects.create_csv_export.assert_called_once_with(
            'NAME', expected_export_parameters)

    @patch('signals.apps.reporting.management.commands.export_signals_csv.CSVExport', autospec=True)
    def test_week_export_cli_handling(self, mocked_model):
        mocked_model.objects = MagicMock()
        cmd = 'export_signals_csv NAME --isoyear 2019 --isoweek 48 '\
            '--categories [[main,cat_a],[main,cat_b]]'
        call_command(*shlex.split(cmd))

        expected_export_parameters = {
            'isoyear': 2019,
            'isoweek': 48,
            'categories': [
                {'main_slug': 'main', 'sub_slug': 'cat_a'},
                {'main_slug': 'main', 'sub_slug': 'cat_b'},
            ]
        }

        mocked_model.objects.create_csv_export.assert_called_once_with(
            'NAME', expected_export_parameters)

    @patch('signals.apps.reporting.management.commands.export_signals_csv.CSVExport', autospec=True)
    def test_month_export_cli_handling(self, mocked_model):
        mocked_model.objects = MagicMock()
        cmd = 'export_signals_csv NAME --year 2019 --month 12 --categories [[main,cat_b]]'
        call_command(*shlex.split(cmd))

        expected_export_parameters = {
            'year': 2019,
            'month': 12,
            'categories': [{'main_slug': 'main', 'sub_slug': 'cat_b'}]
        }

        mocked_model.objects.create_csv_export.assert_called_once_with(
            'NAME', expected_export_parameters)
