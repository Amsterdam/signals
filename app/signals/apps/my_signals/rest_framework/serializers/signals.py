# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from datapunt_api.rest import HALSerializer
from rest_framework import serializers
from rest_framework.fields import ReadOnlyField, SerializerMethodField

from signals.apps.history.models import Log
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
from signals.apps.signals import workflow
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


class HistoryLogHalSerializer(HALSerializer):
    _status_state_translations = {workflow.HEROPEND: 'Heropend',
                                  workflow.GEANNULEERD: 'Afgesloten',
                                  workflow.AFGEHANDELD: 'Afgesloten',
                                  workflow.REACTIE_GEVRAAGD: 'Vraag aan u verstuurd',
                                  workflow.REACTIE_ONTVANGEN: 'Antwoord van u ontvangen'}

    when = serializers.DateTimeField(source='created_at')
    action = serializers.SerializerMethodField()
    description = serializers.CharField(source='get_description')
    _signal = serializers.UUIDField(source='_signal.uuid')

    class Meta:
        model = Log
        fields = (
            'when',
            'what',
            'action',
            'description',
            '_signal'
        )

    def get_action(self, obj):
        what = obj.what
        if what == 'UPDATE_STATUS':
            action = f'Status gewijzigd naar: {self._status_state_translations.get(obj.extra, "Open")}'
        else:
            action = obj.get_action()
        return action
