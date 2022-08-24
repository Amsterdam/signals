# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from unittest import mock

from django.test import TestCase

from signals.apps.reporting import tasks
from signals.apps.reporting.csv.datawarehouse.tasks import task_clean_datawarehouse_disk


class TestTaskSaveCSVFilesDatawarehouse(TestCase):

    @mock.patch('signals.apps.reporting.tasks.save_csv_files_datawarehouse')
    def test_task_save_csv_files_datawarehouse(self, mocked_save_csv_files_datawarehouse):
        tasks.task_save_csv_files_datawarehouse()

        mocked_save_csv_files_datawarehouse.assert_called_once()


class TestTaskCleanDataWarehouseDisk(TestCase):
    @mock.patch(
        'signals.apps.reporting.services.clean_up_datawarehouse.DataWarehouseDiskCleaner.clean_up', autospec=True)
    def test_task_clean_datawarehouse_disk(self, patched):
        task_clean_datawarehouse_disk()
        patched.assert_called_once()
