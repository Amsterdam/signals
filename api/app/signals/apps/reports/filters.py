# SPDX-License-Identifier: MPL-2.0
# Copyright (C)2021 Gemeente Amsterdam
from django.utils import timezone
from django_filters.rest_framework import FilterSet, filters

from signals.apps.signals import workflow


class SignalsOpenPerCategoryCountFilterSet(FilterSet):
    start = filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='gte')
    end = filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='lte')

    def filter_queryset(self, queryset):
        queryset = queryset.exclude(
            status__state__in=[workflow.AFGEHANDELD, workflow.GEANNULEERD, workflow.GESPLITST]
        ).filter(
            category_assignment__deadline_factor_3__lt=timezone.now()
        )
        return super().filter_queryset(queryset)


class SignalsReopenRequestedPerCategoryCountFilterSet(FilterSet):
    start = filters.IsoDateTimeFilter(field_name='status__created_at', lookup_expr='gte')
    end = filters.IsoDateTimeFilter(field_name='status__created_at', lookup_expr='lte')

    def filter_queryset(self, queryset):
        queryset = queryset.filter(status__state=workflow.VERZOEK_TOT_HEROPENEN)
        return super().filter_queryset(queryset)
