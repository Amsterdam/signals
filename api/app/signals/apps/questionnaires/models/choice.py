# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib.gis.db import models


class Choice(models.Model):
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='choices')
    payload = models.JSONField(blank=True, null=True)

    class Meta:
        order_with_respect_to = 'question'
