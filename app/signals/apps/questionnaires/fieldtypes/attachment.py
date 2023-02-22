# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from abc import ABC

from django.conf import settings

from signals.apps.questionnaires.fieldtypes.base import FieldType
from signals.apps.services.domain.mimetypes import (
    MimeTypeFromContentResolverFactory,
    MimeTypeFromFilenameResolverFactory
)
from signals.apps.services.validator.file import (
    ContentIntegrityValidator,
    FileSizeValidator,
    MimeTypeAllowedValidator,
    MimeTypeIntegrityValidator
)


class Attachment(ABC, FieldType):
    """
    The abstract Attachment class to be used as a base class for all attachment field types.
    """
    # The content of this field is not given by the "user", it is generated in the Attachment upload mechanism for
    # questionnaires.
    submission_schema = {
        'type': 'object',
        'properties': {
            'original_filename': {
                'type': 'string',
            },
            'file_path': {
                'type': 'string',
            },
        },
        'required': [
            'original_filename',
            'file_path'
        ],
    }

    def validate_file(self, file):
        """
        Overwrite this function in the child class to validate the file.
        """
        raise NotImplementedError


class Image(Attachment):
    def validate_file(self, file):
        is_mimetype_allowed = MimeTypeAllowedValidator(
            MimeTypeFromContentResolverFactory(),
            (
                'image/jpeg',
                'image/png',
                'image/gif',
            )
        )
        is_mimetype_allowed(file)

        do_mimetypes_match = MimeTypeIntegrityValidator(
            MimeTypeFromContentResolverFactory(),
            MimeTypeFromFilenameResolverFactory()
        )
        do_mimetypes_match(file)

        is_not_too_big = FileSizeValidator(settings.API_MAX_UPLOAD_SIZE)
        is_not_too_big(file)

        is_image = ContentIntegrityValidator(MimeTypeFromContentResolverFactory())
        is_image(file)
