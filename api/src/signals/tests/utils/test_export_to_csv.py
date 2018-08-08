import csv
import json
import shutil
import os
import tempfile
from unittest import mock

from django.test import testcases, override_settings

from signals.utils import export_to_csv
from signals.tests.factories import SignalFactory, LocationFactory


class TestUtilExportToCSV(testcases.TestCase):

    def setUp(self):
       self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_create_signals_csv(self):
        signal = SignalFactory.create()

        csv_file = export_to_csv.create_signals_csv(self.tmp_dir)

        self.assertEqual(os.path.join(self.tmp_dir, 'signals.csv'), csv_file)

        with open(csv_file) as opened_csv_file:
            reader = csv.DictReader(opened_csv_file)
            for row in reader:
                self.assertEqual(row['id'], str(signal.id))
                self.assertEqual(row['signal_uuid'], str(signal.signal_id))
                self.assertEqual(row['source'], str(signal.source))
                self.assertEqual(row['text'], str(signal.text))
                self.assertEqual(row['text_extra'], str(signal.text_extra))
                self.assertEqual(row['location_id'], str(signal.location_id))
                self.assertEqual(row['status_id'], str(signal.status_id))
                self.assertEqual(row['category_id'], str(signal.category_id))
                self.assertEqual(row['reporter_id'], str(signal.reporter_id))
                self.assertEqual(row['incident_date_start'],
                                 str(signal.incident_date_start))
                self.assertEqual(row['incident_date_end'],
                                 str(signal.incident_date_end))
                self.assertEqual(row['created_at'], str(signal.created_at))
                self.assertEqual(row['updated_at'], str(signal.updated_at))
                self.assertEqual(row['operational_date'], '')
                self.assertEqual(row['expire_date'], '')
                self.assertEqual(row['image'], str(signal.image))
                self.assertEqual(row['upload'], '')
                self.assertDictEqual(json.loads(row['extra_properties']),
                                     signal.extra_properties)

    def test_create_locations_csv(self):
        signal = SignalFactory.create()
        location = signal.location

        csv_file = export_to_csv.create_locations_csv(self.tmp_dir)

        self.assertEqual(os.path.join(self.tmp_dir, 'locations.csv'), csv_file)

        with open(csv_file) as opened_csv_file:
            reader = csv.DictReader(opened_csv_file)
            for row in reader:
                self.assertEqual(row['id'], str(location.id))
                self.assertEqual(row['_signal_id'], str(location._signal_id))
                self.assertEqual(row['lat'], str(location.geometrie.x))
                self.assertEqual(row['lng'], str(location.geometrie.y))
                self.assertEqual(row['stadsdeel'],
                                 str(location.get_stadsdeel_display()))
                self.assertEqual(row['buurt_code'], str(location.buurt_code))
                self.assertDictEqual(json.loads(row['address']),
                                     location.address)
                self.assertEqual(row['address_text'],
                                 str(location.address_text))
                self.assertEqual(row['created_at'], str(location.created_at))
                self.assertEqual(row['updated_at'], str(location.updated_at))
                self.assertEqual(json.loads(row['extra_properties']), None)

    def test_create_reporters_csv(self):
        signal = SignalFactory.create()
        reporter = signal.reporter

        csv_file = export_to_csv.create_reporters_csv(self.tmp_dir)

        self.assertEqual(os.path.join(self.tmp_dir, 'reporters.csv'), csv_file)

        with open(csv_file) as opened_csv_file:
            reader = csv.DictReader(opened_csv_file)
            for row in reader:
                self.assertEqual(row['id'], str(reporter.id))
                self.assertEqual(row['_signal_id'], str(reporter._signal_id))
                self.assertEqual(row['email'], str(reporter.email))
                self.assertEqual(row['phone'], str(reporter.phone))
                self.assertEqual(row['remove_at'], '')
                self.assertEqual(row['created_at'], str(reporter.created_at))
                self.assertEqual(row['updated_at'], str(reporter.updated_at))
                self.assertEqual(json.loads(row['extra_properties']), None)

    def test_create_categories_csv(self):
        signal = SignalFactory.create()
        category = signal.category

        csv_file = export_to_csv.create_categories_csv(self.tmp_dir)

        self.assertEqual(
            os.path.join(self.tmp_dir, 'categories.csv'), csv_file)

        with open(csv_file) as opened_csv_file:
            reader = csv.DictReader(opened_csv_file)
            for row in reader:
                self.assertEqual(row['id'], str(category.id))
                self.assertEqual(row['_signal_id'], str(category._signal_id))
                self.assertEqual(row['main'], str(category.main))
                self.assertEqual(row['sub'], str(category.sub))
                self.assertEqual(row['department'], str(category.department))
                self.assertEqual(row['priority'], '')
                self.assertEqual(row['ml_priority'], '')
                self.assertEqual(row['ml_cat'], str(category.ml_cat))
                self.assertEqual(row['ml_prob'], str(category.ml_prob))
                self.assertEqual(row['ml_cat_all'], '')
                self.assertEqual(row['ml_cat_all_prob'], '')
                self.assertEqual(row['ml_sub_cat'], str(category.ml_sub_cat))
                self.assertEqual(row['ml_sub_prob'], str(category.ml_sub_prob))
                self.assertEqual(row['ml_sub_all'], '')
                self.assertEqual(row['ml_sub_all_prob'], '')
                self.assertEqual(row['created_at'], str(category.created_at))
                self.assertEqual(row['updated_at'], str(category.updated_at))
                self.assertEqual(json.loads(row['extra_properties']), None)

    def test_create_statuses_csv(self):
        signal = SignalFactory.create()
        status = signal.status

        csv_file = export_to_csv.create_statuses_csv(self.tmp_dir)

        self.assertEqual(os.path.join(self.tmp_dir, 'statuses.csv'), csv_file)

        with open(csv_file) as opened_csv_file:
            reader = csv.DictReader(opened_csv_file)
            for row in reader:
                self.assertEqual(row['id'], str(status.id))
                self.assertEqual(row['_signal_id'], str(status._signal_id))
                self.assertEqual(row['text'], str(status.text))
                self.assertEqual(row['user'], str(status.user))
                self.assertEqual(row['target_api'], str(status.target_api))
                self.assertEqual(row['state'], status.get_state_display())
                self.assertEqual(row['extern'], str(status.extern))
                self.assertEqual(row['created_at'], str(status.created_at))
                self.assertEqual(row['updated_at'], str(status.updated_at))
                self.assertEqual(json.loads(row['extra_properties']), None)

    @override_settings(
        DWH_SWIFT_AUTH_URL='dwh_auth_url',
        DWH_SWIFT_USERNAME='dwh_username',
        DWH_SWIFT_PASSWORD='dwh_password',
        DWH_SWIFT_TENANT_NAME='dwh_tenant_name',
        DWH_SWIFT_TENANT_ID='dwh_tenant_id',
        DWH_SWIFT_REGION_NAME='dwh_region_name',
        DWH_SWIFT_CONTAINER_NAME='dwh_container_name',
        DWH_SWIFT_USE_TEMP_URLS='dwh_use_temp_urls',
        DWH_SWIFT_TEMP_URL_KEY='dwh_temp_url_key'
    )
    @mock.patch('signals.utils.export_to_csv.SwiftStorage', autospec=True)
    def test_get_storage_backend(self, mocked_swift_storage):
        mocked_swift_storage_instance = mock.Mock()
        mocked_swift_storage.return_value = mocked_swift_storage_instance

        result = export_to_csv._get_storage_backend()

        self.assertEqual(result, mocked_swift_storage_instance)
        mocked_swift_storage.assert_called_once_with(
            api_auth_url='dwh_auth_url',
            api_username='dwh_username',
            api_key='dwh_password',
            tenant_name='dwh_tenant_name',
            tenant_id='dwh_tenant_id',
            region_name='dwh_region_name',
            container_name='dwh_container_name',
            use_temp_urls='dwh_use_temp_urls',
            temp_url_key='dwh_temp_url_key')
