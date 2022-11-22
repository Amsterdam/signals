# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from rest_framework.serializers import ModelSerializer

from signals.apps.signals.models import Location


class LocationModelSerializer(ModelSerializer):
    class Meta:
        model = Location
        geo_field = 'geometrie'
        fields = (
            'geometrie',
            'address',
            'address_text',
        )
        read_only_fields = (
            'geometrie',
            'address',
            'address_text',
        )
