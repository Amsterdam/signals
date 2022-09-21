# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import os

from django.core.files.uploadedfile import SimpleUploadedFile

from signals.apps.services.domain.filescanner import (
    FileTypeExtensionMismatch,
    FileTypeNotSupported,
    UploadScannerService
)
from signals.test.utils import SignalsBaseApiTestCase


class TestUploadScannerService(SignalsBaseApiTestCase):
    DOC_FILE = os.path.join(os.path.dirname(__file__), '../test-data/sia-ontwerp-testfile.doc')

    JPG_FILE = os.path.join(os.path.dirname(__file__), '../test-data/test.jpg')
    PNG_FILE = os.path.join(os.path.dirname(__file__), '../test-data/test.png')
    GIF_FILE = os.path.join(os.path.dirname(__file__), '../test-data/test.gif')
    SVG_FILE = os.path.join(os.path.dirname(__file__), '../test-data/test.svg')

    IMAGE_FILES = [
        (GIF_FILE, 'image/gif'),
        (JPG_FILE, 'image/jpeg'),
        (PNG_FILE, 'image/png'),
        (SVG_FILE, 'image/svg+xml')
    ]

    def test_scan_images(self):
        for image_file_path, content_type in self.IMAGE_FILES:
            with open(image_file_path, 'rb') as image_file:
                uploaded_file = SimpleUploadedFile(image_file_path, image_file.read(), content_type=content_type)
            UploadScannerService.scan_file(uploaded_file)

    def test_scan_images_FileTypeExtensionMismatch(self):
        for image_file_path, content_type in self.IMAGE_FILES:
            image_file_path_incorrect_extension = f'{image_file_path[:image_file_path.find(".")]}.incorrect'
            with open(image_file_path, 'rb') as image_file:
                uploaded_file = SimpleUploadedFile(image_file_path_incorrect_extension, image_file.read(),
                                                   content_type=content_type)

            with self.assertRaises(FileTypeExtensionMismatch):
                UploadScannerService.scan_file(uploaded_file)

    def test_scan_images_FileTypeNotSupported(self):
        with open(self.DOC_FILE, 'rb') as image_file:
            uploaded_file = SimpleUploadedFile(self.DOC_FILE, image_file.read(), content_type='application/msword')

        with self.assertRaises(FileTypeNotSupported):
            UploadScannerService.scan_file(uploaded_file)
