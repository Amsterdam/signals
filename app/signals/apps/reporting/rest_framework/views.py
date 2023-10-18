# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.reporting.filters import (
    SignalsOpenPerCategoryCountFilterSet,
    SignalsReopenRequestedPerCategoryCountFilterSet
)
from signals.apps.reporting.rest_framework.serializers import ReportSignalsPerCategory
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend


class _PrivateReportViewSet(GenericViewSet):
    authentication_classes = [JWTAuthBackend]
    permission_classes = (SIAPermissions,)
    queryset = Signal.objects.all()
    filter_backends = (DjangoFilterBackend,)
    serializer_class = ReportSignalsPerCategory
    pagination_class = None

    def get_queryset(self):
        return self.filter_queryset(super().get_queryset()).values(
            'category_assignment__category_id',
        ).annotate(
            per_category_count=Count('category_assignment__category_id')
        ).order_by(
            '-per_category_count'
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


class PrivateReportSignalsOpenPerCategoryView(_PrivateReportViewSet):
    """
    Count all Signals that have an "open" state and return a summary per Category.

    It is also possible to filter on a period using the "start" and "end" filters (query params)
    """
    filterset_class = SignalsOpenPerCategoryCountFilterSet


class PrivateReportSignalsReopenRequestedPerCategory(_PrivateReportViewSet):
    """
    Count all Signals that are in the "reopen requested" state and return a summary per Category.

    It is also possible to filter on the period the state change was made using the "start" and
    "end" filters (query params)
    """
    filterset_class = SignalsReopenRequestedPerCategoryCountFilterSet
