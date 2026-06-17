# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Gemeente Amsterdam
from django.contrib.gis.db import models

from signals import settings
from signals.apps.classification.utils import _get_storage_backend
from signals.apps.services.domain.checker_factories import ContentCheckerFactory
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

TRAINING_SET_FILE_MAX_SIZE = 524288000 # 500MB # TODO dertermine later what is neceessary for Amsterdam.
# Depends on if we will use CSV or XLXX files, and how many rows we will need to train the model.

class TrainingSet(models.Model):
    """
    This model represents a training set consisting of a single XLSX file, with a "Main", "Sub" and "Text" column
    """
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    name = models.CharField(max_length=255, null=False, blank=False)

    file = models.FileField(
        upload_to='training_sets/%Y/%m/%d/',
        storage=_get_storage_backend,
        null=False,
        blank=False,
        max_length=255,
        validators=[
            MimeTypeAllowedValidator(
                MimeTypeFromContentResolverFactory(),
                (
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            ),
            MimeTypeIntegrityValidator(
                MimeTypeFromContentResolverFactory(),
                MimeTypeFromFilenameResolverFactory()
            ),
            ContentIntegrityValidator(MimeTypeFromContentResolverFactory(), ContentCheckerFactory()),
            FileSizeValidator(TRAINING_SET_FILE_MAX_SIZE),
        ],
    )
