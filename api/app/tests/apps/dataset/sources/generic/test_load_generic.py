import os
from shutil import copyfile
from tempfile import TemporaryDirectory

from django.test import TestCase

from signals.apps.dataset.sources.shape import ShapeBoundariesLoader
from signals.apps.signals.models import Area, AreaType

THIS_DIR = os.path.dirname(__file__)


class TestGenericAreaLoader(TestCase):
    def setUp(self):
        zip_file_name = 'example_shp.zip'
        zip_file = os.path.join(THIS_DIR, 'data', zip_file_name)
        self.directory = TemporaryDirectory()
        dst_zip = os.path.join(self.directory.name, zip_file_name)
        # copy zip_file to temp dir, download is skipped if the file is already present in dst folder
        copyfile(zip_file, dst_zip)
        params = {
            'type_string': 'GENERIC',
            'url': f'http://dummy/{zip_file_name}',
            'shp': 'Wijken.shp',
            'type': 'test-generic-area-type',
            'code': 'NUMMER',
            'name': 'NAAM',
            'dir': self.directory.name
        }
        self.area_loader = ShapeBoundariesLoader(**params)

    def tearDown(self):
        if self.directory:
            self.directory.cleanup()

    def test_load(self):
        self.assertEqual(Area.objects.count(), 0)
        self.area_loader.load()
        created_areas = set(Area.objects.all().values_list('name', flat=True))
        self.assertEqual(14, len(created_areas))
        area_type = AreaType.objects.get(name='test-generic-area-type')
        self.assertTrue(area_type is not None)
