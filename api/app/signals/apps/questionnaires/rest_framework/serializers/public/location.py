# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from signals.apps.signals.models import Location


class LocationModelSerializer(ModelSerializer):
    stadsdeel = SerializerMethodField()

    class Meta:
        model = Location
        geo_field = 'geometrie'
        fields = (
            'geometrie',
            'address',
            'address_text',
            'stadsdeel',
            'area_name',
        )
        read_only_fields = (
            'geometrie',
            'address',
            'address_text',
            'stadsdeel',
            'area_name',
        )

    def get_stadsdeel(self, obj):
        return obj.get_stadsdeel_display()
