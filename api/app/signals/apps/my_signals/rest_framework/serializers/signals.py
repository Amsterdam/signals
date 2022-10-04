# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from datapunt_api.rest import HALSerializer
from rest_framework.fields import ReadOnlyField, SerializerMethodField

from signals.apps.my_signals.rest_framework.fields.signals import (
    MySignalDetailLinksField,
    MySignalListLinksField
)
from signals.apps.my_signals.rest_framework.serializers.nested.location import (
    _NestedMySignalLocationSerializer
)
from signals.apps.my_signals.rest_framework.serializers.nested.status import (
    _NestedMySignalStatusSerializer
)
from signals.apps.signals.models import Signal


class SignalListSerializer(HALSerializer):
    serializer_url_field = MySignalListLinksField

    _display = SerializerMethodField(method_name='get_display')
    id_display = ReadOnlyField(source='get_id_display')
    status = _NestedMySignalStatusSerializer()

    class Meta:
        model = Signal
        fields = (
            '_links',
            '_display',
            'uuid',
            'id_display',
            'text',
            'status',
            'created_at',
        )
        read_only_fields = fields

    def get_display(self, obj):
        return obj.get_id_display()


class SignalDetailSerializer(SignalListSerializer):
    serializer_url_field = MySignalDetailLinksField

    _display = SerializerMethodField(method_name='get_display')
    id_display = ReadOnlyField(source='get_id_display')
    status = _NestedMySignalStatusSerializer()
    location = _NestedMySignalLocationSerializer()

    class Meta:
        model = Signal
        fields = (
            '_links',
            '_display',
            'uuid',
            'id_display',
            'text',
            'status',
            'location',
            'extra_properties',
            'created_at',
        )
        read_only_fields = fields

    def get_display(self, obj):
        return obj.get_id_display()
