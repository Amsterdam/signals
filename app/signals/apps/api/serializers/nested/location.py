# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2025 Gemeente Amsterdam
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
            'area_name',
            'address',
            'address_text',
            'postcode',
            'geometrie',
            'extra_properties',
            'created_by',
            'bag_validated',
        )
        read_only_fields = (
            'id',
            'created_by',
            'bag_validated',
            'postcode',
        )
        extra_kwargs = {
            'id': {'label': 'ID', },
        }
