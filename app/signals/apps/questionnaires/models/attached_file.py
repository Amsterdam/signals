# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.contrib.gis.db import models

from signals.apps.questionnaires.models.attached_section import AttachedSection
from signals.apps.questionnaires.models.stored_file import StoredFile


class AttachedFile(models.Model):
    """
    Images to be used with an AttachedSection of text.
    """
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    # Actual file on disk is referenced by a AttachedFile instance, allowing
    # for deduplication.
    stored_file = models.ForeignKey(StoredFile, on_delete=models.CASCADE, related_name='attached_files')
    description = models.CharField(max_length=255, null=True, blank=True)
    section = models.ForeignKey(AttachedSection, on_delete=models.CASCADE, related_name='files')

    # created_by, uploaded_at ? (track origin of file)
