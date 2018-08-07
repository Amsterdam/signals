import csv
import json
import shutil
import os
import tempfile

from django.test import testcases

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
