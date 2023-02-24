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


class MimeTypeFromFilenameResolverFactory:
    def __call__(self, filename: str) -> MimeTypeFromFilenameResolver:
        return MimeTypeFromFilenameResolver(filename)


class MimeTypeFromContentResolver:
    def __init__(self, file: File):
        self.file = file

    def __call__(self) -> str:
        for chunk in self.file.chunks(chunk_size=2048):
            mimetype = magic.from_buffer(chunk, mime=True)
            if mimetype == 'image/svg':
                mimetype = 'image/svg+xml'

            return mimetype

        raise MimeTypeResolvingError('Failed to resolve mime type from content!')


class MimeTypeFromContentResolverFactory:
    def __call__(self, file: File) -> MimeTypeFromContentResolver:
        return MimeTypeFromContentResolver(file)
