# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from django.contrib.gis.db import models


class AreaType(models.Model):
    class Meta:
        verbose_name = 'Gebiedstype'
        verbose_name_plural = 'Gebiedstypen'
        ordering = ['code']

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=3000)

    def __str__(self):
        return self.name


class Area(models.Model):
    class Meta:
        verbose_name = 'Gebied'
        verbose_name_plural = 'Gebieden'
        unique_together = ('code', '_type')
        ordering = ['_type', 'code']

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    _type = models.ForeignKey(AreaType, on_delete=models.CASCADE)
    geometry = models.MultiPolygonField()

    def __str__(self):
        return self.name
