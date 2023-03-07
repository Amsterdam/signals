# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from datapunt_api.rest import HALSerializer
from rest_framework import serializers

from signals.apps.history.models import Log


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
