from unittest import mock

from django.core.exceptions import ValidationError
from django.test import testcases

from signals.apps.reporting.csv.horeca import (
    _create_extra_properties_headers,
    _create_extra_properties_row,
    _fix_row_to_match_header_count,
    _fix_rows_to_match_header_count,
    _get_horeca_main_category,
    _to_first_and_last_day_of_the_week,
    create_csv_files,
    create_csv_per_sub_category
)
from signals.apps.signals.models import Category, Signal
from tests.apps.signals.factories import SignalFactory


class TestHoreca(testcases.TestCase):
    def test__to_first_and_last_day_of_the_week(self):
        first, last = _to_first_and_last_day_of_the_week(isoweek=1, isoyear=2019)

        self.assertEqual(first.day, 31)
        self.assertEqual(first.month, 12)
        self.assertEqual(first.year, 2018)

        self.assertEqual(last.day, 7)
        self.assertEqual(last.month, 1)
        self.assertEqual(last.year, 2019)

    def test__fix_row_to_match_header_count(self):
        row = []
        headers = [1, 2, 3]
        new_row = _fix_row_to_match_header_count(row, headers)

        self.assertEqual(len(row), 0)
        self.assertEqual(len(new_row), len(headers))

    def test__fix_rows_to_match_header_count(self):
        rows = [[], [1, ], [1, 2, ], ]
        headers = [1, 2, 3, 4]
        new_rows = _fix_rows_to_match_header_count(rows, headers)

        self.assertEqual(len(rows[0]), 0)
        self.assertEqual(len(rows[1]), 1)
        self.assertEqual(len(rows[2]), 2)

        self.assertEqual(len(new_rows[0]), len(headers))
        self.assertEqual(len(new_rows[1]), len(headers))
        self.assertEqual(len(new_rows[2]), len(headers))

    def test__create_extra_properties_headers(self):
        extra_properties = [{
            'id': 'extra_onderhoud_stoep_straat_en_fietspad',
            'label': 'Hebt u verteld om wat voor soort wegdek het gaat?',
            'answer': 'Tegels 30x30 kleur fietspad',
            'category_url': '/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/onderhoud-stoep-straat-en-fietspad'  # noqa
        }]

        headers = []
        headers = _create_extra_properties_headers(extra_properties, headers)

        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0], 'extra_onderhoud_stoep_straat_en_fietspad')

    def test__create_extra_properties_headers_old_style_extra_properties(self):
        extra_properties = {
            'extra_onderhoud_stoep_straat_en_fietspad': 'test',
        }
        headers = _create_extra_properties_headers(extra_properties)

        self.assertEqual(len(headers), 0)

    def test__create_extra_properties_headers_none_extra_properties(self):
        extra_properties = None
        headers = _create_extra_properties_headers(extra_properties)

        self.assertEqual(len(headers), 0)

    def test__create_extra_properties_row(self):
        extra_properties = [{
            'id': 'extra_onderhoud_stoep_straat_en_fietspad',
            'label': 'Hebt u verteld om wat voor soort wegdek het gaat?',
            'answer': 'Tegels 30x30 kleur fietspad',
            'category_url': '/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/onderhoud-stoep-straat-en-fietspad'  # noqa
        }]

        headers = _create_extra_properties_headers(extra_properties, [])
        row = _create_extra_properties_row(extra_properties, headers)

        self.assertEqual(len(row), len(headers))
        self.assertEqual(row[0], 'Tegels 30x30 kleur fietspad')

    def test__create_extra_properties_row_answer_value(self):
        extra_properties = [{
            'id': 'extra_onderhoud_stoep_straat_en_fietspad',
            'label': 'Hebt u verteld om wat voor soort wegdek het gaat?',
            'answer': {'value': 'Tegels 30x30 kleur fietspad'},
            'category_url': '/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/onderhoud-stoep-straat-en-fietspad'  # noqa
        }]

        headers = _create_extra_properties_headers(extra_properties, [])
        row = _create_extra_properties_row(extra_properties, headers)

        self.assertEqual(len(row), len(headers))
        self.assertEqual(row[0], 'Tegels 30x30 kleur fietspad')

    def test__create_extra_properties_row_answer_unusable(self):
        extra_properties = [{
            'id': 'extra_onderhoud_stoep_straat_en_fietspad',
            'label': 'Hebt u verteld om wat voor soort wegdek het gaat?',
            'answer': {'test': 'Tegels 30x30 kleur fietspad'},
            'category_url': '/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/onderhoud-stoep-straat-en-fietspad'  # noqa
        }]

        headers = _create_extra_properties_headers(extra_properties, [])
        row = _create_extra_properties_row(extra_properties, headers)

        self.assertEqual(len(row), len(headers))
        self.assertEqual(row[0], None)

    def test__create_extra_properties_row_old_style_extra_properties(self):
        extra_properties = {
            'extra_onderhoud_stoep_straat_en_fietspad': 'test',
        }

        headers = _create_extra_properties_headers(extra_properties, [])
        row = _create_extra_properties_row(extra_properties, headers)

        self.assertEqual(len(row), 0)

    def test__create_extra_properties_row_none_extra_properties(self):
        extra_properties = None

        headers = _create_extra_properties_headers(extra_properties, [])
        row = _create_extra_properties_row(extra_properties, headers)

        self.assertEqual(len(row), 0)

    def test__get_horeca_main_category(self):
        main_category = _get_horeca_main_category()

        self.assertEqual(main_category.slug, 'overlast-bedrijven-en-horeca')
        self.assertIsNone(main_category.parent_id)

    def test_create_csv_per_sub_category_invalid_category(self):
        main_category = _get_horeca_main_category()

        with self.assertRaises(ValidationError):
            create_csv_per_sub_category(main_category, '/tmp', 1, 2019)

    def test_create_csv_per_sub_category_invalid_sub_category(self):
        main_category = _get_horeca_main_category()
        category = Category.objects.filter(
            parent_id__isnull=False
        ).exclude(
            parent_id=main_category.pk
        ).first()

        with self.assertRaises(NotImplementedError):
            create_csv_per_sub_category(category, '/tmp', 1, 2019)

    def test_create_csv_files(self):
        csv_files = create_csv_files(isoweek=1, isoyear=2019)

        self.assertGreater(len(csv_files), 0)

    @mock.patch.dict('os.environ', {'SWIFT_ENABLED': 'true'}, clear=True)
    @mock.patch('signals.apps.reporting.csv.horeca.HorecaCSVExport', autospec=True)
    def test_create_csv_files_save(self, patched_model):
        # Usage of Django storage means the difference between local and remote
        # storage is abstracted away, so the previously 2 tests were merged.
        patched_model.uploaded_file = mock.MagicMock()
        patched_model.uploaded_file.save = mock.MagicMock()

        # create a Signal with a horeca sub-category
        main_category = _get_horeca_main_category()
        category = Category.objects.filter(
            parent_id__isnull=False, parent_id=main_category.pk).first()

        SignalFactory.create(category_assignment__category=category)
        self.assertEqual(Signal.objects.count(), 1)

        # Check that the storage backend is called, and that shutil.copy is not.
        csv_files = create_csv_files(isoweek=1, isoyear=2019)

        self.assertEqual(len(csv_files), 7)
