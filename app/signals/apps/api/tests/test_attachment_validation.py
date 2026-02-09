# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
"""
Test uploads, specifically test the filetype sniffing. Note we are not testing
the permissions system of SIA/Signalen, hence the usage of superusers to write
to private endpoints
"""
import os
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APILiveServerTestCase

from signals.apps.signals.factories import AttachmentFactory, SignalFactory
from signals.apps.signals.models import Note
from signals.test.utils import SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)

DOC_FILE = os.path.join(THIS_DIR, 'test-data', 'sia-ontwerp-testfile.doc')
PDF_FILE = os.path.join(THIS_DIR, 'test-data', 'sia-ontwerp-testfile.pdf')
JPG_FILE = os.path.join(THIS_DIR, 'test-data', 'test.jpg')
PNG_FILE = os.path.join(THIS_DIR, 'test-data', 'test.png')
GIF_FILE = os.path.join(THIS_DIR, 'test-data', 'test.gif')

ALLOWED = [
    (GIF_FILE, 'image/gif'),
    (JPG_FILE, 'image/jpeg'),
    (PNG_FILE, 'image/png')
]
DISALLOWED = [(DOC_FILE, 'application/msword'), (PDF_FILE, 'application/pdf')]


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

    def test_upload_allowed_private_with_public_field(self):
        self.client.force_authenticate(user=self.superuser)
        for filename, content_type in ALLOWED:
            with open(filename, 'rb') as allowed_file:
                allowed = SimpleUploadedFile(filename, allowed_file.read(), content_type=content_type)
                response = self.client.post(self.private_upload_url, data={'file': allowed, 'public': True})
            self.assertEqual(response.status_code, 201)

    def test_upload_allowed_private_with_caption_field(self):
        self.client.force_authenticate(user=self.superuser)
        for filename, content_type in ALLOWED:
            with open(filename, 'rb') as allowed_file:
                allowed = SimpleUploadedFile(filename, allowed_file.read(), content_type=content_type)
                response = self.client.post(self.private_upload_url, data={'file': allowed, 'caption': 'Allowed'})
            self.assertEqual(response.status_code, 201)

    def test_upload_allowed_private_with_public_and_caption_fields(self):
        self.client.force_authenticate(user=self.superuser)
        for filename, content_type in ALLOWED:
            with open(filename, 'rb') as allowed_file:
                allowed = SimpleUploadedFile(filename, allowed_file.read(), content_type=content_type)
                response = self.client.post(
                    self.private_upload_url,
                    data={'file': allowed, 'public': True, 'caption': 'Allowed'}
                )
            self.assertEqual(response.status_code, 201)

    def test_put_attachment_public_and_caption_fields(self):
        caption = 'Allowed'
        attachment = AttachmentFactory.create(_signal=self.signal, public=False, caption=None)
        self.client.force_authenticate(user=self.superuser)
        response = self.client.put(
            self.private_upload_url + f'{attachment.pk}',
            data={'public': True, 'caption': caption}
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertTrue(body.get('public'))
        self.assertEqual(body.get('caption'), caption)

    def test_patch_attachment_public_field(self):
        attachment = AttachmentFactory.create(_signal=self.signal, public=False, caption=None)
        self.client.force_authenticate(user=self.superuser)
        response = self.client.patch(
            self.private_upload_url + f'{attachment.pk}',
            data={'public': True}
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertTrue(body.get('public'))

    def test_patch_attachment_caption_field(self):
        caption = 'Allowed'
        attachment = AttachmentFactory.create(_signal=self.signal, public=False, caption=None)
        self.client.force_authenticate(user=self.superuser)
        response = self.client.patch(
            self.private_upload_url + f'{attachment.pk}',
            data={'caption': caption}
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body.get('caption'), caption)

    def test_patch_attachment_public_and_caption_field(self):
        caption = 'Allowed'
        attachment = AttachmentFactory.create(_signal=self.signal, public=False, caption=None)
        self.client.force_authenticate(user=self.superuser)
        response = self.client.patch(
            self.private_upload_url + f'{attachment.pk}',
            data={'caption': caption, 'public': True}
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body.get('caption'), caption)
        self.assertTrue(body.get('public'))

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


class TestAttachmentConcurrency(APILiveServerTestCase):
    public_signals_endpoint = '/signals/v1/public/signals/'
    public_attachments_endpoint = public_signals_endpoint + '{uuid}/attachments/'

    def setUp(self):
        self.signal = SignalFactory.create()
        self.public_upload_url = self.public_attachments_endpoint.format(uuid=self.signal.uuid)

    def _upload(self, file_info) -> None:
        with open(file_info[0], 'rb') as allowed_file:
            allowed = SimpleUploadedFile(file_info[0], allowed_file.read(), content_type=file_info[1])
            self.client.post(self.public_upload_url, data={'file': allowed})

    def test_concurrent_uploads(self):
        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.map(self._upload, ALLOWED)

        self.assertEqual(self.signal.attachments.all().count(), len(ALLOWED))
        self.assertEqual(Note.objects.filter(_signal=self.signal).count(), len(ALLOWED))
