# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2024 Delta10 B.V.
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, override_settings

from signals.apps.media.storages import ProtectedFileSystemStorage


@override_settings(PROTECTED_FILE_SYSTEM_STORAGE=True)
class DownloadFileTestCase(TestCase):
    def setUp(self):
        self.storage = ProtectedFileSystemStorage(base_url='http://localhost:8000/signals/media/')

    def test_missing_signature(self):
        # Test with missing 't' or 's' parameter
        response = self.client.get('/signals/media/test.txt')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content, b'No signature provided')

    def test_bad_signature(self):
        # Test with an invalid signature
        response = self.client.get('/signals/media/test.txt?t=some_time&s=some_signature')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content, b'Bad signature')

    @override_settings(DEBUG=True)
    def test_debug_mode_file_serving(self):
        # Test serving the file in DEBUG mode
        with patch('signals.apps.media.views.serve') as mock_serve:
            mock_serve.return_value = HttpResponse('File content')
            response = self.client.get(self.storage.url('test.txt'))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b'File content')
            mock_serve.assert_called_once()

    @override_settings(DEBUG=False)
    def test_production_mode_file_serving(self):
        # Test serving the file in production mode
        with patch('signals.apps.media.views.mimetypes.guess_type') as mock_mimetype:
            mock_mimetype.return_value = 'text/plain', None
            response = self.client.get(self.storage.url('test.txt'))
            self.assertEqual(response.status_code, 200)
            self.assertIn('test.txt', response['X-Sendfile'])
            self.assertEqual(response['Content-Type'], 'text/plain')
