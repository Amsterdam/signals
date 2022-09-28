# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.contrib.gis.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class AttachedSection(models.Model):
    """
    Section of text with title and possible images
    
    This model represents extra information for users of question / questionnaires.
    """
    title = models.CharField(max_length=255)
    text = models.TextField()

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # order

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
