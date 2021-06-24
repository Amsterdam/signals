# SPDX-License-Identifier: MPL-2.0
# Copyright (C)2021 Gemeente Amsterdam
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.reporting.filters import (
    SignalsOpenPerCategoryCountFilterSet,
    SignalsReopenRequestedPerCategoryCountFilterSet
)
from signals.apps.reporting.rest_framework.serializers import ReportSignalsPerCategory
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend


class PrivateReportViewSet(viewsets.GenericViewSet):
    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    pagination_class = None

    queryset = Signal.objects.all()

    filter_backends = (DjangoFilterBackend, )
    filterset_class = None

    def annotate_queryset(self, queryset):
        """
        This will make sure the queryset contains all the information needed to generate the report
        A count of all Signals per category, ordered by the total Signals in a category
        """
        return queryset.values(
            'category_assignment__category_id',
        ).annotate(
            per_category_count=Count('category_assignment__category_id')
        ).order_by(
            '-per_category_count'
        )

    @action(detail=False, url_path=r'signals/open', methods=['GET', ],
            filterset_class=SignalsOpenPerCategoryCountFilterSet, serializer_class=ReportSignalsPerCategory)
    def signals_open_per_category(self, *args, **kwargs):
        """
        Count all Signals that have a "open" state and return a summary per Category.

        It is also possible to filter on a period using the "start_date" and "end_date" filters (query params)
        """
        queryset = self.annotate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)

    @action(detail=False, url_path=r'signals/reopen-requested', methods=['GET', ],
            filterset_class=SignalsReopenRequestedPerCategoryCountFilterSet, serializer_class=ReportSignalsPerCategory)
    def signals_reopen_requested_per_category(self, *args, **kwargs):
        """
        Count all Signals that are in the "reopen requested" state and return a summary per Category.

        It is also possible to filter on the period the state change was made using the "start_date" and
        "end_date" filters (query params)
        """
        queryset = self.annotate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)
