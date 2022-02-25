# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging

from datapunt_api.rest import HALPagination
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from signals.apps.api import app_settings
from signals.apps.api.generics import mixins
from signals.apps.api.generics.pagination import LinkHeaderPagination
from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.serializers import (
    SignalContextGeoSerializer,
    SignalContextReporterSerializer,
    SignalContextSerializer
)
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend

logger = logging.getLogger(__name__)


class SignalContextViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = SignalContextSerializer
    serializer_detail_class = SignalContextSerializer

    pagination_class = HALPagination

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    def get_queryset(self, *args, **kwargs):
        return Signal.objects.filter_for_user(user=self.request.user)

    def near(self, request, pk=None):
        signal = self.get_object()

        signals_for_geography_qs = Signal.objects.annotate(
            distance_from_point=Distance('location__geometrie', signal.location.geometrie),
        ).filter(
            (Q(parent__isnull=True) & Q(children__isnull=True)) | Q(parent__isnull=False),
            distance_from_point__lte=app_settings.SIGNAL_CONTEXT_GEOGRAPHY_RADIUS,
            category_assignment__category_id=signal.category_assignment.category.pk,
            created_at__gte=(
                timezone.now() - timezone.timedelta(weeks=app_settings.SIGNAL_CONTEXT_GEOGRAPHY_CREATED_DELTA_WEEKS)
            ),
        ).exclude(pk=signal.pk)

        paginator = LinkHeaderPagination(page_query_param='geopage', page_size=4000)
        page = paginator.paginate_queryset(signals_for_geography_qs, self.request, view=self)
        if page is not None:
            serializer = SignalContextGeoSerializer(page, many=True, context=self.get_serializer_context())
            return paginator.get_paginated_response(serializer.data)

        serializer = SignalContextGeoSerializer(page, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    def reporter(self, request, pk=None):
        signal = self.get_object()
        if signal.reporter.email:
            signals_for_reporter_qs = Signal.objects.select_related(
                'category_assignment',
                'category_assignment__category',
                'status',
            ).prefetch_related(
                'feedback',
                'category_assignment__category__departments'
            ).filter(
                parent__isnull=True
            ).filter_reporter(
                email=signal.reporter.email
            ).order_by('-created_at')
        else:
            raise NotFound(detail=f'Signal {pk} has no reporter contact detail.')

        page = self.paginate_queryset(signals_for_reporter_qs)
        if page is not None:
            serializer = SignalContextReporterSerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)

        serializer = SignalContextReporterSerializer(signals_for_reporter_qs, many=True,
                                                     context=self.get_serializer_context())
        return Response(serializer.data)
