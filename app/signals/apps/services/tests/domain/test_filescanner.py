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
    PDF_FILE = os.path.join(os.path.dirname(__file__), '../test-data/sia-ontwerp-testfile.pdf')

    ALLOWED_FILES = [
        (GIF_FILE, 'image/gif'),
        (JPG_FILE, 'image/jpeg'),
        (PNG_FILE, 'image/png'),
        (SVG_FILE, 'image/svg+xml'),
        (PDF_FILE, 'application/pdf'),
    ]

    def test_scan_files(self):
        for file_path, content_type in self.ALLOWED_FILES:
            with open(file_path, 'rb') as file:
                uploaded_file = SimpleUploadedFile(file_path, file.read(), content_type=content_type)
            UploadScannerService.scan_file(uploaded_file)

    def test_scan_files_FileTypeExtensionMismatch(self):
        for file_path, content_type in self.ALLOWED_FILES:
            file_path_incorrect_extension = f'{file_path[:file_path.find(".")]}.incorrect'
            with open(file_path, 'rb') as file:
                uploaded_file = SimpleUploadedFile(file_path_incorrect_extension, file.read(),
                                                   content_type=content_type)

            with self.assertRaises(FileTypeExtensionMismatch):
                UploadScannerService.scan_file(uploaded_file)

    def test_scan_files_FileTypeNotSupported(self):
        with open(self.DOC_FILE, 'rb') as file:
            uploaded_file = SimpleUploadedFile(self.DOC_FILE, file.read(), content_type='application/msword')

        with self.assertRaises(FileTypeNotSupported):
            UploadScannerService.scan_file(uploaded_file)
