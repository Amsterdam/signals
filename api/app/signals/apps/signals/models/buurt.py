# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.contrib.gis.db import models


class Buurt(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    id = models.CharField(max_length=14)
    vollcode = models.CharField(max_length=4)
    naam = models.CharField(max_length=40)

    class Meta:
        db_table = 'buurt_simple'
