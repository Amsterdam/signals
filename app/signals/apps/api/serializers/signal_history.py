# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from datapunt_api.rest import HALSerializer
from rest_framework import serializers

from signals.apps.history.models import Log
from signals.apps.signals.models import History, Signal


class HistoryHalSerializer(HALSerializer):
    """
    Serializer for the history based on the signals_history_view, defined in signals.history (Database view)
    """
    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())
    who = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()

    def get_who(self, obj):
        return obj.get_who()

    def get_description(self, obj):
        return obj.get_description()

    def get_action(self, obj):
        return obj.get_action()

    class Meta:
        model = History
        fields = (
            'identifier',
            'when',
            'what',
            'action',
            'description',
            'who',
            '_signal',
        )


class HistoryLogHalSerializer(HALSerializer):
    """
    Serializer for the history based on the history_log, defined in history.log (Database table generated from model)
    """
    _signal = serializers.IntegerField(source='_signal_id')
    action = serializers.CharField(source='get_action')
    description = serializers.CharField(source='get_description')
    when = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Log
        fields = (
            'identifier',
            'when',
            'what',
            'action',
            'description',
            'who',
            '_signal',
        )
