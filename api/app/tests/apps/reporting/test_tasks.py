# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from unittest import mock

from django.test import TestCase

from signals.apps.reporting import tasks


class TestTaskSaveCSVFilesDatawarehouse(TestCase):

    @mock.patch('signals.apps.reporting.tasks.save_csv_files_datawarehouse')
    def test_task_save_csv_files_datawarehouse(self, mocked_save_csv_files_datawarehouse):
        tasks.task_save_csv_files_datawarehouse()

        mocked_save_csv_files_datawarehouse.assert_called_once()
