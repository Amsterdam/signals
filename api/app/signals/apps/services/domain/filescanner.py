# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Check file types, both for fresh uploads and stored files.
"""
import mimetypes

import magic

ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/gif']


class BadFileError(Exception):
    pass


class UploadScannerService:
    def _get_mime_from_extension(uploaded_file):
        return mimetypes.guess_type(uploaded_file.name)[0]  # not interested in encoding

    @staticmethod
    def _get_mime_from_contents(uploaded_file):
        for chunk in uploaded_file.chunks(chunk_size=2048):
            return magic.from_buffer(chunk, mime=True)  # only interested in the start of a file

    def scan_file(uploaded_file):
        """
        Return file if of known and acceptable type, else raise BadFileError.
        """
        seen = set()
        seen.add(UploadScannerService._get_mime_from_extension(uploaded_file))
        seen.add(UploadScannerService._get_mime_from_contents(uploaded_file))

        if len(seen) == 1 and list(seen)[0] in ALLOWED_MIME_TYPES:
            return uploaded_file

        if len(seen) > 1:
            msg = 'File content does not match extension and or content-type header. Upload rejected!'
        elif len(seen) == 1 and list(seen)[0] not in ALLOWED_MIME_TYPES:
            msg = f'Only {" ".join(ALLOWED_MIME_TYPES)} are accepted. Upload rejected!'
        elif len(seen) == 0:
            msg = 'File type could not be determined. Upload rejected!'

        raise BadFileError(msg)
