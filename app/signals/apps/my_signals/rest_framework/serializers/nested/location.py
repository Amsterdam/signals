# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from rest_framework.serializers import ModelSerializer

from signals.apps.api.generics.mixins import WithinBoundingBoxValidatorMixin
from signals.apps.signals.models import Location


class _NestedMySignalLocationSerializer(WithinBoundingBoxValidatorMixin, ModelSerializer):
    class Meta:
        model = Location
        geo_field = 'geometrie'
        fields = (
            'address',
            'address_text',
            'geometrie',
        )
        read_only_fields = fields
