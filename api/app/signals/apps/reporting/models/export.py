# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.contrib.gis.db import models

from signals.apps.reporting.utils import _get_storage_backend

storage = _get_storage_backend(using='horeca')


class HorecaCSVExport(models.Model):
    class Meta:
        ordering = ('-isoyear', '-isoweek', '-created_at')

    created_by = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    isoweek = models.IntegerField()
    isoyear = models.IntegerField()
    uploaded_file = models.FileField(upload_to='exports/%Y', storage=storage)
