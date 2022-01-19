# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Test uploads, specifically test the filetype sniffing. Note we are not testing
the permissions system of SIA/Signalen, hence the usage of superusers to write
to private endpoints
"""
import os
from itertools import chain
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL.Image import DecompressionBombError

from signals.apps.services.domain.filescanner import (
    FileRejectedError,
    FileTypeExtensionMismatch,
    FileTypeNotSupported,
    UploadScannerService
)
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


class TestUploadedFileScannerViaAPI(SignalsBaseApiTestCase):
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
        When an image exceeds a the MAX_IMAGE_PIXELS PIL will protect against potential DOS attacks caused by
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

            response_json = response.json()
            self.assertIn('file', response_json)
            self.assertEqual(1, len(response_json['file']))
            self.assertIn('decompression bomb DOS attack', response_json['file'][0])


class TestUploadScannerService(TestCase):
    def test__get_mime_from_extension(self):
        for filename, content_type in chain(ALLOWED, DISALLOWED):
            with open(filename, 'rb') as disallowed_file:
                suf = SimpleUploadedFile(filename, disallowed_file.read(), content_type=content_type)
                mime_type = UploadScannerService._get_mime_from_extension(suf)

                self.assertEqual(content_type, mime_type)

    def test__get_mime_from_extension_with_no_extension(self):
        with open(GIF_FILE, 'rb') as file:
            suf = SimpleUploadedFile('no-extension', file.read(), content_type='image/gif')
            mime_type = UploadScannerService._get_mime_from_extension(suf)
            self.assertEqual(mime_type, None)

    def test__get_mime_from_content(self):
        for filename, content_type in chain(ALLOWED, DISALLOWED):
            with open(filename, 'rb') as file:
                suf = SimpleUploadedFile(filename, file.read(), content_type=content_type)
                mime_type = UploadScannerService._get_mime_from_content(suf)

                self.assertEqual(mime_type, content_type)

    def test__get_mime_from_content_zero_length(self):
        suf = SimpleUploadedFile('empty.jpg', b'', content_type='image/jpg')
        mime_type = UploadScannerService._get_mime_from_content(suf)

        self.assertEqual(mime_type, 'application/x-empty')

    def test_scan_file_allowed(self):
        for filename, content_type in ALLOWED:
            with open(filename, 'rb') as file:
                suf = SimpleUploadedFile(filename, file.read(), content_type=content_type)
                UploadScannerService.scan_file(suf)

    def test_scan_file_disallowed(self):
        for filename, content_type in DISALLOWED:
            with open(filename, 'rb') as file:
                suf = SimpleUploadedFile(filename, file.read(), content_type=content_type)
                with self.assertRaises(FileRejectedError):
                    UploadScannerService.scan_file(suf)

    def test_scan_file_disallowed_content_does_not_match_extension_i(self):
        with open(DOC_FILE, 'rb') as disallowed_file:
            suf = SimpleUploadedFile('not-actual.jpg', disallowed_file.read(), content_type='image/jpg')
            with self.assertRaises(FileTypeExtensionMismatch):
                UploadScannerService.scan_file(suf)

    def test_scan_file_disallowed_content_does_not_match_extension_ii(self):
        with open(GIF_FILE, 'rb') as allowed_file:
            suf = SimpleUploadedFile('not-actual.jpg', allowed_file.read(), content_type='image/jpg')
            with self.assertRaises(FileTypeExtensionMismatch):
                UploadScannerService.scan_file(suf)

    def test_scan_file_disallowed_raises_filetype_not_supported(self):
        with open(DOC_FILE, 'rb') as disallowed_file:
            suf = SimpleUploadedFile(DOC_FILE, disallowed_file.read(), content_type='application/msword')
            with self.assertRaises(FileTypeNotSupported):
                UploadScannerService.scan_file(suf)

    def test_scan_file_disallowed_no_extension(self):
        # Note: a file without extension will get a mimetype of None in the
        # _get_mime_from_extension method. The _get_mime_from_content will
        # itself derive a non-None extension and the error will be content does
        # not match extension. (Just to document the behavior.)
        with open(GIF_FILE, 'rb') as allowed_file:
            suf = SimpleUploadedFile('not-extension', allowed_file.read(), content_type='image/gif')
            with self.assertRaises(FileTypeExtensionMismatch):
                UploadScannerService.scan_file(suf)

    def test_scan_file_disallowed_empty(self):
        # Note: empty files are labeled: 'application/x-empty' by python-magic
        # hence this case looks like a file with incorrect content given the
        # extension. (Just to document the behavior.)
        suf = SimpleUploadedFile('image.jpg', b'', content_type='image/jpg')
        with self.assertRaises(FileTypeExtensionMismatch):
            UploadScannerService.scan_file(suf)

    @patch('PIL.Image.MAX_IMAGE_PIXELS', 1)
    def test_pil_DecompressionBombError(self):
        """
        When an image exceeds a the MAX_IMAGE_PIXELS PIL will protect against potential DOS attacks caused by
        “decompression bombs”. When the MAX_IMAGE_PIXELS been exceeded PIL will log a DecompressionBombWarning, if the
        image pixels exceed twice the MAX_IMAGE_PIXELS PIL will raise a DecompressionBombError.

        More information can be found on:
            https://pillow.readthedocs.io/en/stable/reference/Image.html?highlight=MAX_IMAGE_PIXELS#PIL.Image.open
        """
        for filename, content_type in ALLOWED:
            with open(filename, 'rb') as file:
                suf = SimpleUploadedFile(filename, file.read(), content_type=content_type)
                with self.assertRaises(DecompressionBombError):
                    UploadScannerService.scan_file(suf)
