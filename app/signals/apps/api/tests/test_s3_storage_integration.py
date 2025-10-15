# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.
import os

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from moto import mock_aws
from storages.backends import s3

from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Attachment
from signals.apps.signals.tests.attachment_helpers import small_gif
from signals.apps.signals.workflow import GEMELD
from signals.test.utils import SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)


@mock_aws
@override_settings(
        S3_STORAGE_ENABLED=True,
        AWS_STORAGE_BUCKET_NAME="test-bucket",
        AWS_S3_REGION_NAME="us-east-1",
        AWS_S3_ENDPOINT_URL=None,
        AWS_ACCESS_KEY_ID="testing",
        AWS_SECRET_ACCESS_KEY="testing",
    )
class TestS3StorageIntegration(SignalsBaseApiTestCase):
    list_endpoint = "/signals/v1/public/signals/"
    detail_endpoint = list_endpoint + "{uuid}"
    attachment_endpoint = detail_endpoint + "/attachments"

    def setUp(self):
        super().setUp()

        self.storage = s3.S3Storage()
        self.bucket = self.storage.connection.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
        self.bucket.create()

        self.create_attachment_schema = self.load_json_schema(
            os.path.join(
                THIS_DIR,
                'json_schema',
                'post_signals_v1_public_signals_attachment.json'
            )
        )

    def test_s3_upload_attachment(self):
        signal = SignalFactory.create(status__state=GEMELD)

        data = {"file": SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')}

        response = self.client.post(self.attachment_endpoint.format(uuid=signal.uuid), data)

        self.assertEqual(201, response.status_code)
        self.assertJsonSchema(self.create_attachment_schema, response.json())

        attachment = Attachment.objects.last()
        self.assertEqual("image/gif", attachment.mimetype)
