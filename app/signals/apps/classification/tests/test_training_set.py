import tempfile
from unittest import mock

from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from signals.apps.classification.models import TrainingSet


class TrainingSetTestCase(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.test_file = SimpleUploadedFile(
            'test_data_set.xlsx',
            b'',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self._storage_patch = mock.patch.object(
            TrainingSet._meta.get_field('file'),
            'storage',
            FileSystemStorage(location=self.tmp_dir),
        )
        self._storage_patch.start()

    def tearDown(self):
        for training_set in TrainingSet.objects.all():
            training_set.file.delete()
        self._storage_patch.stop()

    def test_create_training_set(self):
        training_set = TrainingSet.objects.create(
            name='test_training_set',
            file=self.test_file,
        )

        self.assertEqual(TrainingSet.objects.count(), 1)
        self.assertEqual(training_set.name, 'test_training_set')
        self.assertIsNotNone(training_set.file)
