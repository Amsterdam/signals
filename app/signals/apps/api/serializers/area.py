# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from datapunt_api.serializers import HALSerializer
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from signals.apps.signals.models import Area, AreaType


class AreaTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaType
        fields = ('name', 'code', )


class AreaGeoSerializer(GeoFeatureModelSerializer):
    geometry = GeometryField()

    type = AreaTypeSerializer(source='_type')

    class Meta:
        model = Area
        id_field = False
        geo_field = 'geometry'
        fields = ('name', 'code', 'type', )


class AreaSerializer(HALSerializer):
    type = AreaTypeSerializer(source='_type')
    bbox = serializers.SerializerMethodField()

    class Meta:
        model = Area
        fields = ('name', 'code', 'type', 'bbox', )

    @extend_schema_field({
        'type': 'array',
        'minItems': 4,
        'maxItems': 4,
        'items': {
            'type': 'number',
            'format': 'float',
        },
        'example': [4.728764, 52.278987, 5.068003, 52.431229],
        'description': 'Bounding box as [min_x, min_y, max_x, max_y]',
    })
    def get_bbox(self, obj: Area) -> tuple[float, float, float, float] | None:
        if obj.geometry:
            return obj.geometry.extent

        return None
