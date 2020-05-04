from rest_framework_gis import serializers
from rest_framework_gis.fields import GeometryField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from signals.apps.signals.models import Area, AreaType


class AreaTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaType
        fields = ('name', 'code')


class AreaGeoSerializer(GeoFeatureModelSerializer):
    geometry = GeometryField()

    type = AreaTypeSerializer(source='_type')

    class Meta:
        model = Area
        id_field = False
        geo_field = 'geometry'
        fields = ('id', 'name', 'code', 'type', )
