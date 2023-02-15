# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib.gis.db import models


class PublicSignalGeographyFeature(models.Model):
    """
    A materialized view is used to query information for the public geography endpoint

    Migration:
        api/app/signals/apps/signals/migrations/0164_materialized_view_public_signals_geography_feature_collection.py
    """
    id = models.BigIntegerField(primary_key=True)
    uuid = models.UUIDField()
    geometry = models.PointField()
    state = models.CharField(max_length=36)
    child_category_id = models.BigIntegerField()
    child_category_is_public_accessible = models.BooleanField()
    parent_category_id = models.BigIntegerField()
    created_at = models.DateTimeField()
    feature = models.JSONField()

    # No changes to this database view please!
    def save(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError

    class Meta:
        managed = False
        db_table = 'public_signals_geography_feature_collection'
