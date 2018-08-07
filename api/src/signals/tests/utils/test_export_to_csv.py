import csv
import shutil
import tempfile

from django.test import testcases

from signals.utils import export_to_csv
from signals.tests.factories import SignalFactory


class TestUtilExportToCSV(testcases.TestCase):

    def setUp(self):
       self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_create_signals_csv(self):
        signal = SignalFactory.create()

        csv_file = export_to_csv.create_signals_csv(self.tmp_dir)

        with open(csv_file) as opened_csv_file:
            reader = csv.DictReader(opened_csv_file)
            for row in reader:
                self.assertEqual(row['id'], str(signal.id))
                self.assertEqual(row['signal_id'], str(signal.signal_id))
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
                self.assertEqual(row['extra_properties'],
                                 str(signal.extra_properties))
