# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from django.contrib.gis.db import models

from change_log.logger import ChangeLogger


class TestModel(models.Model):
    title = models.CharField(max_length=16)
    text = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)

    logger = ChangeLogger()
