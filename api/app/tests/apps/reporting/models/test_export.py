import io
from unittest import mock

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase as DjangoTestCase

from signals.apps.reporting.models import CSVExport
from signals.apps.reporting.models.export import SignalCSVWriter
from signals.apps.signals.models import Signal
from tests.apps.signals.factories import CategoryFactory, SignalFactory


class SignalsExportTestDataMixin:
    def setUp(self):
        # create test category hierarchy
        self.main_cat = CategoryFactory(name='main', parent=None)
        self.cat_a = CategoryFactory(name='cat_a', parent=self.main_cat)
        self.cat_b = CategoryFactory(name='cat_b', parent=self.main_cat)

        self.cat_url_a = f'/signals/v1/public/terms/categories/{self.main_cat.slug}/subcategories/{self.cat_a.slug}'  # noqa E501
        self.cat_url_b = f'/signals/v1/public/terms/categories/{self.main_cat.slug}/subcategories/{self.cat_b.slug}'  # noqa E501

        # create some test signals in those categories
        extra_properties_a = [
            {
                'id': 'A',
                'label': 'extra_property_a',
                'answer': 'a',
            },
            {
                'id': 'B',
                'label': 'extra_property_b',
                'answer': {
                    'value': 'b'
                }

            },
        ]
        extra_properties_b = [
            {
                'id': 'C',
                'label': 'extra_property_c',
                'answer': {
                    'label': 'c'
                }
            }
        ]
        SignalFactory.create_batch(
            size=5,
            category_assignment__category=self.cat_a,
            extra_properties=extra_properties_a
        )
        SignalFactory.create_batch(
            size=4,
            category_assignment__category=self.cat_b,
            extra_properties=extra_properties_b
        )

        # Export parameters for daily, weekly, monthly exports
        all_test_categories = [{'main_slug': self.main_cat.slug, 'sub_slug': '*'}]
        self.daily_export_parameters = {
            'year': 2019,
            'month': 12,
            'day': 31,
            'categories': all_test_categories,
            'areas': ['TBD', 'TBD'],
        }
        self.weekly_export_parameters = {
            'isoyear': 2019,
            'isoweek': 48,
            'categories': all_test_categories,
            'areas': ['TBD', 'TBD'],
        }
        self.monthly_export_parameters = {
            'year': 2019,
            'month': 12,
            'categories': all_test_categories,
            'areas': ['TBD', 'TBD'],
        }


class TestCSVExportModel(SignalsExportTestDataMixin, DjangoTestCase):
    def test_create_instance(self):
        self.test_csv = SimpleUploadedFile(
            'test.csv',
            b'A,B\na,b'
        )

        self.assertEqual(CSVExport.objects.count(), 0)

        c = CSVExport(
            created_by='a.mbtenaar@example.com',
            uploaded_file=self.test_csv,
            export_parameters=self.daily_export_parameters
        )
        c.full_clean()
        c.save()

        self.assertEqual(CSVExport.objects.count(), 1)


class TestSignalsCSVWriter(SignalsExportTestDataMixin, DjangoTestCase):
    def test_signals_csv_writer_extra_properties_headers(self):
        f = mock.MagicMock()
        writer = SignalCSVWriter(f, Signal.objects.all())

        # Check that the extra column names are correctly derived
        extra_column_names = writer.get_extra_column_names()
        extra_column_names.sort()
        self.assertEqual(extra_column_names, ['A', 'B', 'C'])

    def test_signals_csv_writer_iterate_queryset(self):
        f = mock.MagicMock()
        writer = SignalCSVWriter(f, Signal.objects.all())

        n_signals = Signal.objects.count()
        rows = list(writer.iterate_queryset())
        self.assertEqual(len(rows), n_signals)

    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('signals.apps.reporting.models.export.DictWriter', autospec=True)
    def test_signals_csv_writer_happy_flow(self, mocked_dict_writer, mocked_open):
        dict_writer_instance = mock.MagicMock()
        mocked_dict_writer.return_value = dict_writer_instance

        with open('test.csv', 'w') as f:
            writer = SignalCSVWriter(f, Signal.objects.all())
            writer.writerows()

        # check that writing the rows works
        column_names = SignalCSVWriter.STANDARD_COLUMN_NAMES + ['A', 'B', 'C']

        mocked_open.assert_called_once_with('test.csv', 'w')
        mocked_dict_writer.assert_called_once_with(
            f, column_names, extrasaction='ignore', restval='')
        dict_writer_instance.writerows.called_once()

    def test_check_csv_export_contents(self):
        # pass a buffer to the SignalCSVWriter, check its contents after writing
        # the export to it
        f = io.StringIO()
        writer = SignalCSVWriter(f, Signal.objects.all())
        writer.writerows()

        f.seek(0)
        lines = f.readlines()
        self.assertEqual(len(lines), Signal.objects.count())


class TestCSVModelManager(SignalsExportTestDataMixin, DjangoTestCase):
    def test_create_csv_export(self):
        self.assertEqual(CSVExport.objects.count(), 0)
        CSVExport.objects.create_csv_export(
            basename='testbasename',
            export_parameters=self.daily_export_parameters
        )

        CSVExport.objects.create_csv_export(
            basename='testbasename',
            export_parameters=self.weekly_export_parameters
        )

        CSVExport.objects.create_csv_export(
            basename='testbasename',
            export_parameters=self.monthly_export_parameters
        )

        self.assertEqual(CSVExport.objects.count(), 3)

    def test_create_csv_export_bad_parameters(self):
        # Check that the Django ValidationErrors are correctly propagated
        # (validation itself is tested in tests.apps.reporting.models.test_mixin)
        bad_data = self.daily_export_parameters
        bad_data['isoweek'] = 12

        with self.assertRaises(DjangoValidationError):
            CSVExport.objects.create_csv_export(
                basename='testbasename',
                export_parameters=bad_data
            )
