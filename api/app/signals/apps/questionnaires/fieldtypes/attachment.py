# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from abc import ABC

from signals.apps.questionnaires.fieldtypes.base import FieldType
from signals.apps.services.domain.filescanner import UploadScannerService


class Attachment(ABC, FieldType):
    """
    The abstract Attachment class to be used as a base class for all attachment field types.
    """
    # The content of this field is not given by the "user", it is generated in the Attachment uploade mechanism for
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
        UploadScannerService.scan_file(file)
