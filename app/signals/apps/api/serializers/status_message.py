# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from rest_framework import serializers

from signals.apps.signals.models import StatusMessage


class StatusMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusMessage
        fields = ['id', 'title', 'text', 'active', 'state', 'categories', 'updated_at', 'created_at']
