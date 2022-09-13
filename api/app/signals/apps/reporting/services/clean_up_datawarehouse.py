# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import os
import pathlib
from datetime import date, timedelta

from django.utils import timezone


class BadDataRoot(Exception):
    pass


class DataWarehouseDiskCleaner:
    """
    Clean-up disk storage used by datawarehouse CSV dumps.

    Note: this uses can only be used for local disks not for remote file storage
    like SWIFT storage.
    """
    GLOB_PATTERNS = [
        '[0-9]' * 6 + '*.csv',
        '[0-9]' * 8 + '_' + '[0-9]' * 6 + '*.zip',
    ]

    @staticmethod
    def _data_directories(data_root):
        return data_root.rglob('[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]/')

    @staticmethod
    def _find_data_directories(data_root, start_date, end_date):
        """
        Yield data directories, under `data_root` starting at `start_date` and up to and including `end_date`.
        """
        if data_root.match('/'):
            raise BadDataRoot('Cannot look for data exports under filesystem root!')
        data_directories = DataWarehouseDiskCleaner._data_directories(data_root)

        found = []
        for path in data_directories:
            if not path.is_dir():
                continue

            year_s, month_s, day_s = path.parts[-3:]
            to_consider = date(int(year_s), int(month_s), int(day_s))
            if not (start_date <= to_consider <= end_date):
                continue
            found.append(path)

        return found

    @staticmethod
    def _delete_files_from_directory(path, dry_run):
        """
        Delete known CSV exports and Zip archives from given data directory.
        """
        removed = []
        for glob_pattern in DataWarehouseDiskCleaner.GLOB_PATTERNS:
            for p in path.rglob(glob_pattern):
                if p.is_file():
                    removed.append(p)
                    if not dry_run:
                        os.remove(p)
        return removed

    @staticmethod
    def clean_up(data_root, keep_n_days=30, dry_run=False):
        """
        Clean-up CSV dumps and Zip archives under the `data_root` directory.
        """
        start_date = date(2020, 1, 1)  # Zipped CSV dumps were not available as a feature at this date.
        end_date = (timezone.now() - timedelta(days=keep_n_days)).date()

        scanned = []
        removed = []
        for path in DataWarehouseDiskCleaner._find_data_directories(pathlib.Path(data_root), start_date, end_date):
            scanned.append(path)
            removed.extend(DataWarehouseDiskCleaner._delete_files_from_directory(path, dry_run))

        return scanned, removed
