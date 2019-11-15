from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase as DjangoTestCase
from freezegun import freeze_time

from signals.apps.reporting.models import CSVExport
from signals.apps.reporting.models.export import SignalCSVWriter
from signals.apps.signals.models import Signal
from tests.apps.signals.factories import CategoryFactory, SignalFactory


class TestCSVExportModel(DjangoTestCase):
    def setUp(self):
        self.test_csv = SimpleUploadedFile(
            'test.csv',
            b'A,B\na,b'
        )
        all_test_categories = [{'main_slug': '*', 'sub_slug': '*'}]
        self.daily_export_parameters = {
            'year': 2019,
            'month': 12,
            'day': 31,
            'categories': all_test_categories,
        }

    def test_create_instance(self):
        self.assertEqual(CSVExport.objects.count(), 0)

        c = CSVExport(
            created_by='a.mbtenaar@example.com',
            uploaded_file=self.test_csv,
            export_parameters=self.daily_export_parameters
        )
        c.full_clean()
        c.save()

        self.assertEqual(CSVExport.objects.count(), 1)


class TestSignalsCSVWriter(DjangoTestCase):
    def setUp(self):
        # create test category hierarchy
        self.main_cat = CategoryFactory(name='main', parent=None)
        self.cat_a = CategoryFactory(name='cat_a', parent=self.main_cat)
        self.cat_b = CategoryFactory(name='cat_b', parent=self.main_cat)

        self.cat_url_a = f'/signals/v1/public/terms/categories/{self.main_cat.slug}/subcategories/{self.cat_a.slug}'  # noqa
        self.cat_url_b = f'/signals/v1/public/terms/categories/{self.main_cat.slug}/subcategories/{self.cat_b.slug}'  # noqa


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

        # Daily CSV export
        all_test_categories = [{'main_slug': self.main_cat.slug, 'sub_slug': '*'}]
        self.daily_export_parameters = {
            'year': 2019,
            'month': 12,
            'day': 31,
            'categories': all_test_categories,
            'areas': ['TBD', 'TBD'],
        }

    def test_signals_csv_writer_happy_flow(self):
        m = mock.mock_open()
        with mock.patch('__main__.open', m):
            with open('test.csv', 'w') as f:
                writer = SignalCSVWriter(f, Signal.objects.all())

                # Check that the extra column names are correctly derived
                extra_column_names = writer.get_extra_column_names()
                extra_column_names.sort()
                self.assertEqual(extra_column_names, ['A', 'B', 'C'])

                # Check that qeuryset iteration works:
                n_signals = Signal.objects.count()
                rows = list(writer.iterate_queryset())
                self.assertEqual(len(rows), n_signals)

                # check that writing the rows works
                writer.writerows()


class TestCSVModelManager(DjangoTestCase):
    def setUp(self):
        # create test category hierarchy
        self.main_cat = CategoryFactory(name='main', parent=None)
        self.cat_a = CategoryFactory(name='cat_a', parent=self.main_cat)
        self.cat_b = CategoryFactory(name='cat_b', parent=self.main_cat)

        all_test_categories = [{'main_slug': self.main_cat.slug, 'sub_slug': '*'}]

        # create some test signals in those categories
        SignalFactory.create_batch(size=5, category_assignment__category=self.cat_a)
        SignalFactory.create_batch(size=4, category_assignment__category=self.cat_b)

        # Daily CSV export
        self.daily_export_parameters = {
            'year': 2019,
            'month': 12,
            'day': 31,
            'categories': all_test_categories,
            'areas': ['TBD', 'TBD'],
        }

    def test_create_daily_csv_export(self):
        self.assertEqual(CSVExport.objects.count(), 0)
        CSVExport.objects.create_csv_export(
            basename='testbasename',
            export_parameters=self.daily_export_parameters
        )
        self.assertEqual(CSVExport.objects.count(), 1)
