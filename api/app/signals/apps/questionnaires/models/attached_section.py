# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.contrib.gis.db import models

from signals.apps.questionnaires.models.illustrated_text import IllustratedText


class AttachedSection(models.Model):
    """
    Section of text with title and possible images

    This model represents extra information for users of question / questionnaires.
    """
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    header = models.CharField(max_length=255, null=True, blank=True)
    text = models.TextField(null=True, blank=True)

    illustrated_text = models.ForeignKey(IllustratedText, related_name='sections', on_delete=models.CASCADE)

    class Meta:
        order_with_respect_to = 'illustrated_text'
