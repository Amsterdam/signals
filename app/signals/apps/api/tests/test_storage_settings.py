# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, storages
from django.test import SimpleTestCase, override_settings
from moto import mock_aws
from storages.backends.s3 import S3Storage

S3_STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3.S3Storage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}


class TestDefaultStorageConfiguration(SimpleTestCase):
    """
    Django removed DEFAULT_FILE_STORAGE in 5.1, so the storage backend is selected
    through the STORAGES setting instead. These tests assert that the backends
    settings.py can put in STORAGES['default'] actually resolve and work, which
    nothing else covers: the S3 and Azure branches in settings.py are guarded by
    environment variables that are not set in the test environment.
    """

    def test_storages_declares_both_required_aliases(self) -> None:
        # Django raises ImproperlyConfigured when 'staticfiles' is missing, and
        # 'default' is what default_storage resolves to.
        self.assertIsInstance(storages['default'], FileSystemStorage)
        self.assertIsNotNone(storages['staticfiles'])


@mock_aws
@override_settings(
    STORAGES=S3_STORAGES,
    AWS_STORAGE_BUCKET_NAME='test-bucket',
    AWS_S3_REGION_NAME='us-east-1',
    AWS_S3_ENDPOINT_URL=None,
    AWS_ACCESS_KEY_ID='testing',
    AWS_SECRET_ACCESS_KEY='testing',
)
class TestS3AsDefaultStorage(SimpleTestCase):
    def setUp(self) -> None:
        super().setUp()
        S3Storage().connection.Bucket('test-bucket').create()

    def test_default_storage_resolves_to_the_s3_backend(self) -> None:
        self.assertIsInstance(storages['default'], S3Storage)

    def test_a_file_round_trips_through_the_default_storage(self) -> None:
        name = storages['default'].save('upgrade-check.txt', ContentFile(b'hello'))

        # No cleanup needed: moto discards the mocked bucket when the test ends. Note
        # that addCleanup() would run after mock_aws has been torn down, and would
        # therefore try to reach the real S3.
        with storages['default'].open(name) as stored_file:
            self.assertEqual(stored_file.read(), b'hello')
