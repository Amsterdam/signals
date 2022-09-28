# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.contrib.gis.db import models


class StoredFile(models.Model):
    """
    Image stored for use in Questionnaires app.
    """
    # This model exists to allow deduplication of images that are used in
    # potentially a large number of questionnaires.
    file = models.FileField(
        upload_to='questionnaires/%Y/%m/%d/',
        null=False,
        blank=False,
        max_length=255
    )