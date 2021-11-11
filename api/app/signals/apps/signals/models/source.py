# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django.contrib.gis.db import models


class Source(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(max_length=3000)
    order = models.PositiveIntegerField(null=True)
    is_active = models.BooleanField(default=False)

    # When is_public is set to True this Source can only be used when creating Signals using the public endpoint
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ('order', 'name', )

    def __str__(self):
        return self.name
