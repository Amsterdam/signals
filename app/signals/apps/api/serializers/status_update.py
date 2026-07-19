# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from signals.apps.signals import workflow
from signals.apps.signals.models import Status

STATUS_UPDATE_MAPPING = {
    workflow.BEHANDELING: 'IN_PROGRESS',
    workflow.AFGEHANDELD: 'RESOLVED',
    workflow.HEROPEND: 'IN_PROGRESS',
}


class StatusUpdateFeedQuerySerializer(serializers.Serializer):
    source = serializers.CharField(max_length=128)  # type: ignore[assignment]
    after = serializers.IntegerField(min_value=0, required=False, default=0)
    limit = serializers.IntegerField(min_value=1, required=False)

    def validate_source(self, value: str) -> str:
        if value not in settings.STATUS_UPDATE_FEED_ALLOWED_SOURCES:
            raise PermissionDenied('Status updates are not enabled for this source.')
        return value

    def validate(self, attrs: dict) -> dict:
        max_page_size = settings.STATUS_UPDATE_FEED_MAX_PAGE_SIZE
        limit = attrs.get('limit', max_page_size)
        if limit > max_page_size:
            raise serializers.ValidationError({
                'limit': f'Ensure this value is less than or equal to {max_page_size}.'
            })
        attrs['limit'] = limit
        return attrs


class StatusUpdateSerializer(serializers.Serializer):
    signal_id = serializers.UUIDField(source='_signal.uuid', read_only=True)
    status = serializers.SerializerMethodField()
    changed_at = serializers.DateTimeField(source='created_at', read_only=True)
    event_id = serializers.IntegerField(source='pk', read_only=True)

    @extend_schema_field(OpenApiTypes.STR)
    def get_status(self, obj: Status) -> str:
        return STATUS_UPDATE_MAPPING[obj.state]


class StatusUpdateFeedResponseSerializer(serializers.Serializer):
    items = StatusUpdateSerializer(many=True)
    next_cursor = serializers.IntegerField()
