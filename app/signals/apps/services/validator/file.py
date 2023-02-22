# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.core.exceptions import ValidationError
from django.core.files import File

from signals.apps.services.domain.images import IsImageChecker
from signals.apps.services.domain.mimetypes import (
    MimeTypeFromContentResolverFactory,
    MimeTypeFromFilenameResolverFactory,
    MimeTypeResolvingError
)
from signals.apps.services.domain.pdf import IsPdfChecker


class MimeTypeAllowedValidator:
    def __init__(self, mimetype_resolver_factory: MimeTypeFromContentResolverFactory, allowed_mimetypes):
        self.mimetype_resolver_factory = mimetype_resolver_factory
        self.allowed_mimetypes = allowed_mimetypes

    def __call__(self, value: File):
        try:
            resolve_mimetype = self.mimetype_resolver_factory(value)
            mimetype = resolve_mimetype()
            if mimetype not in self.allowed_mimetypes:
                raise ValidationError(f"Files of type '{mimetype}' are not allowed!")
        except MimeTypeResolvingError:
            raise ValidationError('MimeType resolving failed!')


class MimeTypeIntegrityValidator:
    def __init__(
            self,
            mimetype_from_content_resolver_factory: MimeTypeFromContentResolverFactory,
            mimetype_from_filename_resolver_factory: MimeTypeFromFilenameResolverFactory,
    ):
        self.mimetype_from_content_resolver_factory = mimetype_from_content_resolver_factory
        self.mimetype_from_filename_resolver_factory = mimetype_from_filename_resolver_factory

    def __call__(self, value: File):
        resolve_mime_from_content = self.mimetype_from_content_resolver_factory(value)
        mime_from_content = resolve_mime_from_content()

        resolve_mime_from_filename = self.mimetype_from_filename_resolver_factory(value.name)
        mime_from_filename = resolve_mime_from_filename()

        if mime_from_content != mime_from_filename:
            raise ValidationError(f"'{mime_from_content}' does not match filename extension!")


class ContentIntegrityValidator:
    def __init__(self, mimetype_resolver_factory: MimeTypeFromContentResolverFactory):
        self.mimetype_resolver_factory = mimetype_resolver_factory

    def __call__(self, value: File):
        resolve_mimetype = self.mimetype_resolver_factory(value)
        mimetype = resolve_mimetype()

        create_content_checker = self.ContentCheckerFactory()
        is_valid = create_content_checker(mimetype, value)
        if is_valid is not None and is_valid() is False:
            raise ValidationError("File is not a valid image or pdf document!")

    class ContentCheckerFactory:
        def __call__(self, mimetype: str, file):
            if mimetype in ('image/jpeg', 'image/png', 'image/gif'):
                return IsImageChecker(file)
            elif mimetype == 'application/pdf':
                return IsPdfChecker(file)

            return None


class FileSizeValidator:
    def __init__(self, max_size: int):
        self.max_size = max_size

    def __call__(self, value: File):
        if value.size > self.max_size:
            raise ValidationError(f"File size of {value.size} is more than the allowed size {self.max_size}!")
