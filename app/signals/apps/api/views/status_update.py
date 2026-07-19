# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from signals.apps.api.generics.permissions import SIAStatusUpdateFeedPermission
from signals.apps.api.serializers.status_update import (
    STATUS_UPDATE_MAPPING,
    StatusUpdateFeedQuerySerializer,
    StatusUpdateFeedResponseSerializer,
    StatusUpdateSerializer
)
from signals.apps.signals.models import Status
from signals.auth.backend import JWTAuthBackend
from signals.schema import GenericErrorSerializer


class StatusUpdateFeedView(APIView):
    authentication_classes = [JWTAuthBackend]
    permission_classes = (SIAStatusUpdateFeedPermission,)
    serializer_class = StatusUpdateFeedResponseSerializer

    @extend_schema(
        parameters=[StatusUpdateFeedQuerySerializer],
        responses={
            200: StatusUpdateFeedResponseSerializer,
            400: OpenApiTypes.OBJECT,
            401: GenericErrorSerializer,
            403: GenericErrorSerializer,
        },
        description='Read status changes for signals from an enabled source using a cursor.',
    )
    def get(self, request: Request) -> Response:
        query_serializer = StatusUpdateFeedQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        source = query_serializer.validated_data['source']
        after = query_serializer.validated_data['after']
        limit = query_serializer.validated_data['limit']

        status_rows = list(
            Status.objects
            .filter(_signal__source=source, pk__gt=after)
            .select_related('_signal')
            .only('pk', 'state', 'created_at', '_signal__uuid')
            .order_by('pk')[:limit]
        )
        next_cursor = status_rows[-1].pk if status_rows else after
        visible_status_rows = [row for row in status_rows if row.state in STATUS_UPDATE_MAPPING]

        return Response({
            'items': StatusUpdateSerializer(visible_status_rows, many=True).data,
            'next_cursor': next_cursor,
        })
