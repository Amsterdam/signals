# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Check file types for fresh uploads.
"""
import logging
import mimetypes

import magic

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/gif']


class FileRejectedError(Exception):
    pass


class FileTypeNotSupported(FileRejectedError):
    pass


class FileTypeExtensionMismatch(FileRejectedError):
    pass


class FileTypeNotRecognized(FileRejectedError):
    pass


class UploadScannerService:
    @staticmethod
    def _get_mime_from_extension(uploaded_file):
        return mimetypes.guess_type(uploaded_file.name)[0]  # not interested in encoding

    @staticmethod
    def _get_mime_from_content(uploaded_file):
        for chunk in uploaded_file.chunks(chunk_size=2048):
            return magic.from_buffer(chunk, mime=True)  # only interested in the start of a file

    @staticmethod
    def scan_file(uploaded_file):
        """
        Return file if of known and acceptable type, else raise BadFileError.
        """
        # Special cases:
        # - empty files -> rejected with a FileTypeExtensionMismatch exception
        # - zero length files -> rejected with a FileTypeExtensionMismatch exception
        seen = set()
        seen.add(UploadScannerService._get_mime_from_extension(uploaded_file))
        seen.add(UploadScannerService._get_mime_from_content(uploaded_file))

        if len(seen) == 1 and list(seen)[0] in ALLOWED_MIME_TYPES:
            return uploaded_file

        if len(seen) > 1:
            msg = 'File content does not match extension. Upload rejected!'
            raise FileTypeExtensionMismatch(msg)
        elif len(seen) == 1 and list(seen)[0] not in ALLOWED_MIME_TYPES:
            msg = f'Only {" ".join(ALLOWED_MIME_TYPES)} are accepted. Upload rejected!'
            raise FileTypeNotSupported(msg)
        elif len(seen) == 0:
            # This is a catch-all that should not be hit, but if we do a warning
            # is logged.
            logger.warning(f'File {uploaded_file.name} could not be recognized.')
            msg = 'File type could not be determined. Upload rejected!'
            raise FileTypeNotRecognized(msg)
