# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.contrib.gis.db import models


class StoredFile(models.Model):
    """
    Image stored for use in Questionnaires app.
    """
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    # This model exists to allow deduplication of images that are used in
    # potentially a large number of questionnaires.
    file = models.FileField(
        upload_to='questionnaires/%Y/%m/%d/',
        null=False,
        blank=False,
        max_length=255
    )

    def get_reference_count(self):
        """
        Number of AttachedFile instances referencing this StoredFile instance.
        """
        from signals.apps.questionnaires.models.attached_file import AttachedFile
        return AttachedFile.filter(stored_file=self).count()
