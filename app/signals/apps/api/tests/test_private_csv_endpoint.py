# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import os
import shutil
import tempfile
from unittest import mock

from django.contrib.auth.models import Permission
from django.core.files.storage import FileSystemStorage
from freezegun import freeze_time
from rest_framework import status

from signals.apps.reporting.csv import datawarehouse
from signals.test.utils import SIAReadWriteUserMixin, SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)


class TestPrivateCSVEndpoint(SIAReadWriteUserMixin, SignalsBaseApiTestCase):
    csv_endpoint = '/signals/v1/private/csv/'

    def setUp(self):
        self.csv_tmp_dir = tempfile.mkdtemp()
        self.file_backend_tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.csv_tmp_dir)
        shutil.rmtree(self.file_backend_tmp_dir)

    def _add_report_permission(self):
        # sia_signal_report
        read_perm = Permission.objects.get(
            codename='sia_signal_report'
        )
        self.sia_read_write_user.user_permissions.add(read_perm)

    def test_get_csv_no_permission(self):
        self.client.force_authenticate(user=self.sia_read_write_user)
        response = self.client.get(f'{self.csv_endpoint}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch.dict('os.environ', {}, clear=True)
    @mock.patch('signals.apps.reporting.csv.utils._get_storage_backend')
    @freeze_time('2020-09-10T12:00:00+00:00')
    def test_get_zip(self, mocked_get_storage_backend):
        mocked_get_storage_backend.return_value = FileSystemStorage(location=self.file_backend_tmp_dir)
        datawarehouse.save_and_zip_csv_files_endpoint()
        self._add_report_permission()
        self.client.force_authenticate(user=self.sia_read_write_user)
        with self.settings(DWH_MEDIA_ROOT=self.file_backend_tmp_dir):
            response = self.client.get(f'{self.csv_endpoint}')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
