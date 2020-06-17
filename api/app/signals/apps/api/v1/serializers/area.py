from datapunt_api.serializers import HALSerializer
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

    def get_bbox(self, obj):
        if obj.geometry:
            return obj.geometry.extent
