# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.core.exceptions import ValidationError
from django.core.files import File
from django.utils.deconstruct import deconstructible

from signals.apps.services.domain.checker_factories import ContentCheckerFactory
from signals.apps.services.domain.mimetypes import (
    MimeTypeFromContentResolverFactory,
    MimeTypeFromFilenameResolverFactory,
    MimeTypeResolvingError
)


@deconstructible
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
            raise ValidationError('Mime type resolving failed!')


@deconstructible
class MimeTypeIntegrityValidator:
    def __init__(
            self,
            mimetype_from_content_resolver_factory: MimeTypeFromContentResolverFactory,
            mimetype_from_filename_resolver_factory: MimeTypeFromFilenameResolverFactory,
    ):
        self.mimetype_from_content_resolver_factory = mimetype_from_content_resolver_factory
        self.mimetype_from_filename_resolver_factory = mimetype_from_filename_resolver_factory

    def __call__(self, value: File):
        try:
            resolve_mime_from_content = self.mimetype_from_content_resolver_factory(value)
            mime_from_content = resolve_mime_from_content()
        except MimeTypeResolvingError:
            raise ValidationError('Failed to resolve mime type from file content!')

        try:
            resolve_mime_from_filename = self.mimetype_from_filename_resolver_factory(value.name)
            mime_from_filename = resolve_mime_from_filename()
        except MimeTypeResolvingError:
            raise ValidationError('Failed to resolve mime type from filename!')

        if mime_from_content != mime_from_filename:
            raise ValidationError(f"'{mime_from_content}' does not match filename extension!")


@deconstructible
class ContentIntegrityValidator:
    def __init__(
            self,
            mimetype_resolver_factory: MimeTypeFromContentResolverFactory,
            content_checker_factory: ContentCheckerFactory
    ):
        self.mimetype_resolver_factory = mimetype_resolver_factory
        self.content_checker_factory = content_checker_factory

    def __call__(self, value: File):
        resolve_mimetype = self.mimetype_resolver_factory(value)
        try:
            mimetype = resolve_mimetype()
        except MimeTypeResolvingError:
            raise ValidationError("Failed to resolve mime type!")

        is_valid = self.content_checker_factory(mimetype, value)
        if is_valid is not None and is_valid() is False:
            raise ValidationError("File is not valid!")


@deconstructible
class FileSizeValidator:
    def __init__(self, max_size: int):
        self.max_size = max_size

    def __call__(self, value: File):
        if value.size > self.max_size:
            raise ValidationError(f"File size of {value.size} is more than the allowed size {self.max_size}!")
