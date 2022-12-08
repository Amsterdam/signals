# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from django.contrib.gis.db import models


class IllustratedText(models.Model):
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    # Note for the actual text and images see the AttachedSection model.
    title = models.CharField(max_length=255, null=True, blank=True)
