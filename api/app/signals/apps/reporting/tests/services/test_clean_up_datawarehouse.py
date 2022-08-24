# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import pathlib
from datetime import date, datetime
from unittest.mock import MagicMock, PropertyMock, patch

from django.test import TestCase
from freezegun import freeze_time

from signals.apps.reporting.services.clean_up_datawarehouse import (
    BadDataRoot,
    DataWarehouseDiskCleaner
)


class TestDataWarehouseDiskCleaner(TestCase):
    def test__find_data_directories_not_from_root(self):
        """
        We must not "clean up" starting from filesystem root.
        """
        start_date = date(2020, 1, 1)
        end_date = date(2022, 6, 1)

        with self.assertRaises(BadDataRoot):
            DataWarehouseDiskCleaner._find_data_directories(pathlib.PurePosixPath('/'), start_date, end_date)

    @patch('signals.apps.reporting.services.clean_up_datawarehouse.DataWarehouseDiskCleaner._data_directories',
           autospec=True)
    def test__find_data_directories_matching_directory(self, mocked):
        test_path = MagicMock()
        test_path.is_dir.return_value = True
        test_path.parts = [2022, 2, 2]
        mocked.return_value = [test_path]

        start_date = date(2020, 1, 1)
        end_date = date(2022, 6, 1)

        found = DataWarehouseDiskCleaner._find_data_directories(
            pathlib.PurePosixPath('/not/root'), start_date, end_date)
        self.assertEqual(found, [test_path])

    @patch('signals.apps.reporting.services.clean_up_datawarehouse.DataWarehouseDiskCleaner._data_directories',
           autospec=True)
    def test__find_data_directories_non_matching_directory(self, mocked):
        test_path = MagicMock()
        test_path.is_dir.return_value = True
        test_path.parts = [2019, 2, 2]
        mocked.return_value = [test_path]

        start_date = date(2020, 1, 1)
        end_date = date(2022, 6, 1)

        found = DataWarehouseDiskCleaner._find_data_directories(
            pathlib.PurePosixPath('/not/root'), start_date, end_date)
        self.assertEqual(found, [])

    @patch('signals.apps.reporting.services.clean_up_datawarehouse.DataWarehouseDiskCleaner.GLOB_PATTERNS',
           new_callable=PropertyMock)
    def test___delete_files_from_directory(self, patched):
        patched.return_value = ['/is/not/used/in/test/']

        a = MagicMock()
        a.is_file = MagicMock()
        a.is_file.return_value = True

        b = MagicMock()
        b.is_file = MagicMock()
        b.is_file.return_value = False

        path = MagicMock()
        path.rglob = MagicMock()
        path.rglob.return_value = [a]

        removed = DataWarehouseDiskCleaner._delete_files_from_directory(path, dry_run=True)
        self.assertEqual(removed, [a])

    def AAAAAtest___delete_files_from_directory(self):
        test_path = MagicMock()
        test_file_matching = MagicMock()
        test_file_matching.is_file.return_value = True
        test_file_non_matching = MagicMock()
        test_file_non_matching.is_file.return_value = False
        test_path.rglob = MagicMock()
        test_path.rglob.return_value = [test_file_matching, test_file_non_matching]

        removed = DataWarehouseDiskCleaner._delete_files_from_directory(test_path, dry_run=True)
        self.assertEqual(removed, [test_file_matching])

    @patch('signals.apps.reporting.services.clean_up_datawarehouse.DataWarehouseDiskCleaner._delete_files_from_directory',  # noqa: 501
           autospec=True)
    @patch('signals.apps.reporting.services.clean_up_datawarehouse.DataWarehouseDiskCleaner._find_data_directories',
           autospec=True)
    def test_clean_up(self, patched_finder, patched_deleter):
        patched_finder.return_value = ['scanned']
        patched_deleter.return_value = ['deleted', 'deleted']
        with freeze_time(datetime(2022, 8, 31, 12, 0, 0)):
            scanned, removed = DataWarehouseDiskCleaner.clean_up('/test/data/dir/', dry_run=True)

        patched_finder.assert_called_with(pathlib.Path('/test/data/dir/'), date(2020, 1, 1), date(2022, 8, 1))
        self.assertEqual(scanned, ['scanned'])
        patched_deleter.assert_called_with('scanned', True)
        self.assertEqual(removed, ['deleted', 'deleted'])
