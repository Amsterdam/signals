# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
"""
Test uploads, specifically test the filetype sniffing. Note we are not testing
the permissions system of SIA/Signalen, hence the usage of superusers to write
to private endpoints
"""
import os
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile

from signals.apps.signals.factories import SignalFactory
from signals.test.utils import SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)

DOC_FILE = os.path.join(THIS_DIR, 'test-data', 'sia-ontwerp-testfile.doc')
JPG_FILE = os.path.join(THIS_DIR, 'test-data', 'test.jpg')
PNG_FILE = os.path.join(THIS_DIR, 'test-data', 'test.png')
GIF_FILE = os.path.join(THIS_DIR, 'test-data', 'test.gif')

ALLOWED = [
    (GIF_FILE, 'image/gif'),
    (JPG_FILE, 'image/jpeg'),
    (PNG_FILE, 'image/png')
]
DISALLOWED = [(DOC_FILE, 'application/msword')]


class TestAttachmentValidation(SignalsBaseApiTestCase):
    """
    Test file scanner functionality.
    """
    private_signals_endpoint = '/signals/v1/private/signals/'
    private_attachments_endpoint = private_signals_endpoint + '{pk}/attachments/'

    public_signals_endpoint = '/signals/v1/public/signals/'
    public_attachments_endpoint = public_signals_endpoint + '{uuid}/attachments/'

    def setUp(self):
        self.signal = SignalFactory.create()
        self.private_upload_url = self.private_attachments_endpoint.format(pk=self.signal.id)
        self.public_upload_url = self.public_attachments_endpoint.format(uuid=self.signal.uuid)

    def test_upload_allowed_public(self):
        # Test uploads of files with allowed filetypes with correct content and
        # filename extensions - test public endpoint.
        for filename, content_type in ALLOWED:
            with open(filename, 'rb') as allowed_file:
                allowed = SimpleUploadedFile(filename, allowed_file.read(), content_type=content_type)
                response = self.client.post(self.public_upload_url, data={'file': allowed})
            self.assertEqual(response.status_code, 201)

    def test_upload_allowed_private(self):
        # Private endpoint version of above.
        self.client.force_authenticate(user=self.superuser)
        for filename, content_type in ALLOWED:
            with open(filename, 'rb') as allowed_file:
                allowed = SimpleUploadedFile(filename, allowed_file.read(), content_type=content_type)
                response = self.client.post(self.private_upload_url, data={'file': allowed})
            self.assertEqual(response.status_code, 201)

    def test_upload_disallowed_public(self):
        # Test uploads of disfiles with allowed filetypes with correct content
        # and filename extensions - test public endpoint.
        for filename, content_type in DISALLOWED:
            with open(filename, 'rb') as disallowed_file:
                disallowed = SimpleUploadedFile(filename, disallowed_file.read(), content_type=content_type)
                response = self.client.post(self.public_upload_url, data={'file': disallowed})
            self.assertEqual(response.status_code, 400)

    def test_upload_disallowed_private(self):
        # Private endpoint version of above.
        self.client.force_authenticate(user=self.superuser)
        for filename, content_type in DISALLOWED:
            with open(filename, 'rb') as disallowed_file:
                disallowed = SimpleUploadedFile(filename, disallowed_file.read(), content_type=content_type)
                response = self.client.post(self.private_upload_url, data={'file': disallowed})
            self.assertEqual(response.status_code, 400)

    def test_upload_disallowed_content_does_not_match_extension_public_i(self):
        # Test the file content scanner by uploading a file that has an allowed
        # extension but the actual content of a disallowed filetype - test
        # public endpoint.
        with open(DOC_FILE, 'rb') as disallowed_file:
            renamed = SimpleUploadedFile('not-actual.jpg', disallowed_file.read(), content_type='image/jpg')
            response = self.client.post(self.public_upload_url, data={'file': renamed})
        self.assertEqual(response.status_code, 400)

    def test_upload_disallowed_content_does_not_match_extension_private_i(self):
        # Private endpoint version of above.
        self.client.force_authenticate(user=self.superuser)
        with open(DOC_FILE, 'rb') as disallowed_file:
            renamed = SimpleUploadedFile('not-actual.jpg', disallowed_file.read(), content_type='image/jpg')
            response = self.client.post(self.private_upload_url, data={'file': renamed})
        self.assertEqual(response.status_code, 400)

    def test_upload_disallowed_content_does_not_match_extension_public_ii(self):
        # Test the file content scanner by uploading a file that has an allowed
        # extension but the actual content another type of allowed filetype.
        # Out of an abundance of caution this case is rejected as well - test
        # public endpoint.
        with open(GIF_FILE, 'rb') as allowed_file:
            renamed = SimpleUploadedFile('not-actual.jpg', allowed_file.read(), content_type='image/jpg')
            response = self.client.post(self.public_upload_url, data={'file': renamed})
        self.assertEqual(response.status_code, 400)

    def test_upload_disallowed_content_does_not_match_extension_private_ii(self):
        # Private endpoint version of above.
        self.client.force_authenticate(user=self.superuser)
        with open(GIF_FILE, 'rb') as allowed_file:
            renamed = SimpleUploadedFile('not-actual.jpg', allowed_file.read(), content_type='image/jpg')
            response = self.client.post(self.private_upload_url, data={'file': renamed})
        self.assertEqual(response.status_code, 400)

    @patch('PIL.Image.MAX_IMAGE_PIXELS', 1)
    def test_upload_disallowed_pil_DecompressionBombError(self):
        """
        When an image exceeds the MAX_IMAGE_PIXELS PIL will protect against potential DOS attacks caused by
        “decompression bombs”. When the MAX_IMAGE_PIXELS been exceeded PIL will log a DecompressionBombWarning, if the
        image pixels exceed twice the MAX_IMAGE_PIXELS PIL will raise a DecompressionBombError.

        More information can be found on:
            https://pillow.readthedocs.io/en/stable/reference/Image.html?highlight=MAX_IMAGE_PIXELS#PIL.Image.open
        """
        self.client.force_authenticate(user=self.superuser)
        for filename, content_type in ALLOWED:
            with open(filename, 'rb') as file:
                suf = SimpleUploadedFile(filename, file.read(), content_type=content_type)
                response = self.client.post(self.private_upload_url, data={'file': suf})
            self.assertEqual(response.status_code, 400)
