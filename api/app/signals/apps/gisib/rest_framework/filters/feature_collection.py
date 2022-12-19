# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib.gis.geos import Polygon
from django.db.models import Q
from django_filters.rest_framework import FilterSet, filters


class FeatureCollectionFilterSet(FilterSet):
    id = filters.NumberFilter(field_name='gisib_id')

    bbox = filters.CharFilter()  # min_lon, min_lat, max_lon, max_lat

    def filter_queryset(self, queryset):
        bbox = self.form.cleaned_data.pop('bbox', None)
        if bbox:
            queryset = queryset.filter(Q(geometry__within=Polygon.from_bbox(bbox.split(','))))

        return super().filter_queryset(queryset=queryset)
