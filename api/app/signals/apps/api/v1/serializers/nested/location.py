from signals.apps.api.generics.mixins import NearAmsterdamValidatorMixin
from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.signals.models import Location


class _NestedLocationModelSerializer(NearAmsterdamValidatorMixin, SIAModelSerializer):
    class Meta:
        model = Location
        geo_field = 'geometrie'
        fields = (
            'id',
            'stadsdeel',
            'buurt_code',
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
