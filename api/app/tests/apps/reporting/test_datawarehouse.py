import csv
import json
import os
import shutil
import tempfile
from datetime import datetime
from os import path
from unittest import mock

import pytz
from django.core.files.storage import FileSystemStorage
from django.test import override_settings, testcases

from signals.apps.reporting.csv import datawarehouse
from tests.apps.feedback.factories import FeedbackFactory
from tests.apps.signals.factories import SignalFactory


class TestDatawarehouse(testcases.TestCase):

    def setUp(self):
        self.csv_tmp_dir = tempfile.mkdtemp()
        self.file_backend_tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.csv_tmp_dir)
        shutil.rmtree(self.file_backend_tmp_dir)

    @mock.patch.dict('os.environ', {}, clear=True)
    @mock.patch('signals.apps.reporting.csv.datawarehouse._get_storage_backend')
    def test_save_csv_files_datawarehouse(self, mocked_get_storage_backend):
        # Mocking the storage backend to local file system with tmp directory.
        # In this test case we don't want to make usage of the remote Object
        # Store.
        mocked_get_storage_backend.return_value = FileSystemStorage(
            location=self.file_backend_tmp_dir)

        # Creating a few objects in the database.
        for i in range(3):
            SignalFactory.create()

        datawarehouse.save_csv_files_datawarehouse()

        # Checking if we have files on the correct locations and that they
        # do have some content.
        signals_csv = path.join(self.file_backend_tmp_dir, 'signals.csv')
        locations_csv = path.join(self.file_backend_tmp_dir, 'locations.csv')
        reporters_csv = path.join(self.file_backend_tmp_dir, 'reporters.csv')
        categories_csv = path.join(self.file_backend_tmp_dir, 'categories.csv')
        statuses_csv = path.join(self.file_backend_tmp_dir, 'statuses.csv')
        sla_csv = path.join(self.file_backend_tmp_dir, 'sla.csv')
        self.assertTrue(path.exists(signals_csv))
        self.assertTrue(path.getsize(signals_csv))
        self.assertTrue(path.exists(locations_csv))
        self.assertTrue(path.getsize(locations_csv))
        self.assertTrue(path.exists(reporters_csv))
        self.assertTrue(path.getsize(reporters_csv))
        self.assertTrue(path.exists(categories_csv))
        self.assertTrue(path.getsize(categories_csv))
        self.assertTrue(path.exists(statuses_csv))
        self.assertTrue(path.getsize(statuses_csv))
        self.assertTrue(path.getsize(sla_csv))

    @override_settings(
        DWH_SWIFT_AUTH_URL='dwh_auth_url',
        DWH_SWIFT_USERNAME='dwh_username',
        DWH_SWIFT_PASSWORD='dwh_password',
        DWH_SWIFT_TENANT_NAME='dwh_tenant_name',
        DWH_SWIFT_TENANT_ID='dwh_tenant_id',
        DWH_SWIFT_REGION_NAME='dwh_region_name',
        DWH_SWIFT_CONTAINER_NAME='dwh_container_name'
    )
    @mock.patch.dict(os.environ, {'SWIFT_ENABLED': 'true'})
    @mock.patch('signals.apps.reporting.csv.utils.SwiftStorage', autospec=True)
    def test_get_storage_backend(self, mocked_swift_storage):
        mocked_swift_storage_instance = mock.Mock()
        mocked_swift_storage.return_value = mocked_swift_storage_instance

        result = datawarehouse._get_storage_backend(datawarehouse.get_swift_parameters())

        self.assertEqual(result, mocked_swift_storage_instance)
        mocked_swift_storage.assert_called_once_with(
            api_auth_url='dwh_auth_url',
            api_username='dwh_username',
            api_key='dwh_password',
            tenant_name='dwh_tenant_name',
            tenant_id='dwh_tenant_id',
            region_name='dwh_region_name',
            container_name='dwh_container_name',
            auto_overwrite=True)

    def test_create_signals_csv(self):
        signal = SignalFactory.create()

        csv_file = datawarehouse._create_signals_csv(self.csv_tmp_dir)

        self.assertEqual(path.join(self.csv_tmp_dir, 'signals.csv'), csv_file)

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
                self.assertEqual(row['category_assignment_id'], str(signal.category_assignment_id))
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

                # SIG-2823
                self.assertEqual(row['priority'], str(signal.priority.priority))
                self.assertEqual(row['priority_created_at'], str(signal.priority.created_at))
                self.assertEqual(row['parent'], '')
                self.assertEqual(row['type'], str(signal.type_assignment.name))
                self.assertEqual(row['type_created_at'], str(signal.type_assignment.created_at))

    def test_create_locations_csv(self):
        signal = SignalFactory.create()
        location = signal.location

        csv_file = datawarehouse._create_locations_csv(self.csv_tmp_dir)

        self.assertEqual(path.join(self.csv_tmp_dir, 'locations.csv'),
                         csv_file)

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

        csv_file = datawarehouse._create_reporters_csv(self.csv_tmp_dir)

        self.assertEqual(path.join(self.csv_tmp_dir, 'reporters.csv'),
                         csv_file)

        with open(csv_file) as opened_csv_file:
            reader = csv.DictReader(opened_csv_file)
            for row in reader:
                self.assertEqual(row['id'], str(reporter.id))
                self.assertEqual(row['_signal_id'], str(reporter._signal_id))
                self.assertEqual(row['email'], str(reporter.email))
                self.assertEqual(row['phone'], str(reporter.phone))
                self.assertEqual(row['is_anonymized'], 'False')
                self.assertEqual(row['created_at'], str(reporter.created_at))
                self.assertEqual(row['updated_at'], str(reporter.updated_at))

    def test_create_category_assignments_csv(self):
        signal = SignalFactory.create()
        category_assignment = signal.category_assignment

        csv_file = datawarehouse._create_category_assignments_csv(self.csv_tmp_dir)

        self.assertEqual(path.join(self.csv_tmp_dir, 'categories.csv'),
                         csv_file)

        with open(csv_file) as opened_csv_file:
            reader = csv.DictReader(opened_csv_file)
            for row in reader:
                self.assertEqual(row['id'], str(category_assignment.id))
                self.assertEqual(row['_signal_id'], str(category_assignment._signal_id))
                self.assertEqual(row['main'],
                                 str(category_assignment.category.parent.name))
                self.assertEqual(row['sub'], str(category_assignment.category.name))
                self.assertEqual(row['departments'],
                                 ', '.join(category_assignment.category.departments.values_list(
                                     'name', flat=True)))
                self.assertEqual(row['created_at'], str(category_assignment.created_at))
                self.assertEqual(row['updated_at'], str(category_assignment.updated_at))
                self.assertEqual(json.loads(row['extra_properties']), None)

    def test_create_statuses_csv(self):
        signal = SignalFactory.create()
        status = signal.status

        csv_file = datawarehouse._create_statuses_csv(self.csv_tmp_dir)

        self.assertEqual(path.join(self.csv_tmp_dir, 'statuses.csv'), csv_file)

        with open(csv_file) as opened_csv_file:
            reader = csv.DictReader(opened_csv_file)
            for row in reader:
                self.assertEqual(row['id'], str(status.id))
                self.assertEqual(row['_signal_id'], str(status._signal_id))
                self.assertEqual(row['text'], str(status.text))
                self.assertEqual(row['user'], str(status.user))
                self.assertEqual(row['target_api'], '')
                self.assertEqual(row['state_display'],
                                 status.get_state_display())
                self.assertEqual(row['extern'], str(status.extern))
                self.assertEqual(row['created_at'], str(status.created_at))
                self.assertEqual(row['updated_at'], str(status.updated_at))
                self.assertEqual(json.loads(row['extra_properties']), None)
                self.assertEqual(row['state'], status.state)


class TestFeedbackHandling(testcases.TestCase):
    """Test that KTO feedback is properly processed."""

    def setUp(self):
        self.signal = SignalFactory.create()
        self.feedback_submitted = FeedbackFactory.create(
            _signal=self.signal,
            created_at=datetime(2019, 4, 9, 12, 0, tzinfo=pytz.UTC),
            submitted_at=datetime(2019, 4, 9, 18, 0, 0, tzinfo=pytz.UTC),
            text='Tevreden want mooi weer',
            text_extra='Waarom? Daarom!'
        )
        self.feedback_requested = FeedbackFactory.create(
            _signal=self.signal,
            created_at=datetime(2019, 4, 9, 12, 0, 0),
        )
        self.csv_tmp_dir = tempfile.mkdtemp()

    @mock.patch.dict('os.environ', {'ENVIRONMENT': 'BAD_VALUE'}, clear=True)
    def test_environment_not_properly_set(self):
        with self.assertRaises(EnvironmentError):
            datawarehouse._create_kto_feedback_csv('dummy_location')

    @mock.patch.dict('os.environ', {}, clear=True)
    def test_environment_empty(self):
        with self.assertRaises(EnvironmentError):
            datawarehouse._create_kto_feedback_csv('dummy_location')

    @mock.patch.dict('os.environ', {'ENVIRONMENT': 'PRODUCTION'}, clear=True)
    def test_environment_set(self):
        # filename should contain ENVRIONMENT
        file_name = datawarehouse._create_kto_feedback_csv(self.csv_tmp_dir)
        self.assertEqual(os.path.split(file_name)[-1], 'kto-feedback-PRODUCTION.csv')

        # header and one entry should show up in written file.
        with open(file_name, 'r') as f:
            reader = csv.reader(f)

            self.assertEqual(len(list(reader)), 2)

    @mock.patch.dict('os.environ', {'ENVIRONMENT': 'PRODUCTION'}, clear=True)
    def test_create_(self):
        # filename should contain ENVRIONMENT
        csv_file = datawarehouse._create_kto_feedback_csv(self.csv_tmp_dir)
        self.assertEqual(os.path.join(self.csv_tmp_dir, 'kto-feedback-PRODUCTION.csv'), csv_file)

        # header and one entry should show up in written file.
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader):
                self.assertEqual(row['_signal_id'], str(self.feedback_submitted._signal.id))
                self.assertEqual(row['is_satisfied'], str(self.feedback_submitted.is_satisfied))
                self.assertEqual(row['allows_contact'], str(self.feedback_submitted.allows_contact))
                self.assertEqual(row['text_extra'], self.feedback_submitted.text_extra)
                self.assertEqual(row['created_at'], str(self.feedback_submitted.created_at))
                self.assertEqual(row['submitted_at'], str(self.feedback_submitted.submitted_at))

                self.assertEqual(row['text'], self.feedback_submitted.text)

            self.assertEqual(i, 0)
