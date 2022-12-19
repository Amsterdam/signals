# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib.gis.db import models


class GISIBFeature(models.Model):
    """
    Base GISIB Feature cache class
    """
    gisib_id = models.BigIntegerField()
    geometry = models.PointField()
    properties = models.JSONField()
    raw_feature = models.JSONField()

    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(editable=False, auto_now=True)
