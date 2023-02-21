# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import mimetypes

import magic
from django.core.files import File


class MimeTypeResolvingError(Exception):
    pass


class MimeTypeFromFilenameResolver:
    def __init__(self, filename: str):
        self.filename = filename

    def __call__(self) -> str:
        mimetype_info = mimetypes.guess_type(self.filename)
        if mimetype_info[0] is None:
            raise MimeTypeResolvingError('Failed to guess mime type!')

        return mimetype_info[0]


class MimeTypeFromContentResolver:
    def __init__(self, file: File):
        self.file = file

    def __call__(self) -> str:
        for chunk in self.file.chunks(chunk_size=2048):
            return magic.from_buffer(chunk, mime=True)

        raise MimeTypeResolvingError('Failed to resolve mime type from content!')
