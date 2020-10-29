from signals.apps.api.generics.mixins import WithinBoundingBoxValidatorMixin
from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals.models import Location


class _NestedLocationModelSerializer(WithinBoundingBoxValidatorMixin, SIAModelSerializer):
    class Meta:
        model = Location
        geo_field = 'geometrie'
        fields = (
            'id',
            'stadsdeel',
            'buurt_code',
            'area_type_code',
            'area_code',
            'address',
            'address_text',
            'geometrie',
            'extra_properties',
            'created_by',
            'bag_validated',
        )
        read_only_fields = (
            'id',
            'created_by',
            'bag_validated',
        )
        extra_kwargs = {
            'id': {'label': 'ID', },
        }
