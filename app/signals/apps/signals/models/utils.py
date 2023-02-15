# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.core.exceptions import ValidationError

from signals.apps.services.domain.filescanner import (
    FileTypeExtensionMismatch,
    FileTypeNotSupported,
    UploadScannerService
)


def validate_category_icon(value):
    """
    Use the UploadScannerService to check if the given file is an image

    TODO: Ask if additional checks are required?
    """
    try:
        UploadScannerService.scan_file(value)
    except (FileTypeExtensionMismatch, FileTypeNotSupported) as e:
        raise ValidationError(e)


def upload_category_icon_to(instance, filename):
    """
    Will create the upload to structure for category icons.
    For example:
    - icons/categories/afval/icon.jpg (Parent category)
    - icons/categories/afval/asbest-accu/icon.jpg (Child category)
    """
    file_path = 'icons/categories'
    if instance.is_parent():
        file_path = f'{file_path}/{instance.slug}'
    else:
        file_path = f'{file_path}/{instance.parent.slug}/{instance.slug}'
    return f'{file_path}/{filename}'
