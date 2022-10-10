# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DEFAULT_RENDERERS
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.http import Http404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_501_NOT_IMPLEMENTED
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.api.generics.filters import FieldMappingOrderingFilter
from signals.apps.my_signals.rest_framework.filters.signals import MySignalFilterSet
from signals.apps.my_signals.rest_framework.serializers.signals import (
    SignalDetailSerializer,
    SignalListSerializer
)
from signals.apps.signals.models import Signal


class MySignalsViewSet(DetailSerializerMixin, ReadOnlyModelViewSet):
    renderer_classes = DEFAULT_RENDERERS
    pagination_class = HALPagination

    # TODO: SIG-4757 add login/authentication flow
    authentication_classes = ()

    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    serializer_class = SignalListSerializer
    serializer_detail_class = SignalDetailSerializer

    filter_backends = (DjangoFilterBackend, FieldMappingOrderingFilter,)
    filterset_class = MySignalFilterSet

    ordering = (
        '-created_at',
    )
    ordering_fields = (
        'created_at',
    )
    ordering_field_mappings = {
        'created_at': 'created_at',
    }

    def get_queryset(self, *args, **kwargs):
        """
        Only return signals that are in a specific state and created in the last year

        TODO: SIG-4757 add login/authentication flow
        """
        one_year_ago = timezone.now() - relativedelta(years=1)

        return Signal.objects.filter(
            created_at__gte=one_year_ago  # Only signals from the last 12 months
        ).exclude(
            parent__isnull=False  # Exclude all child signals
        )

    def _feature_enabled(self):
        """
        When the feature is disabled return a 404 not found
        """
        if not settings.FEATURE_FLAGS['MY_SIGNALS_ENABLED']:
            raise Http404

    def list(self, request, *args, **kwargs):
        self._feature_enabled()
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self._feature_enabled()
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, url_path=r'history/?$')
    def history(self, *args, **kwargs):
        """
        Placeholder for the history view of a signal, this will be implemented when ticket SIG-4764 has been refined
        """
        self._feature_enabled()
        return Response(status=HTTP_501_NOT_IMPLEMENTED)
