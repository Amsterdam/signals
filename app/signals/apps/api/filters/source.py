# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django_filters.rest_framework import FilterSet, filters


class PrivateSourceFilterSet(FilterSet):
    can_be_selected = filters.BooleanFilter()
    is_active = filters.BooleanFilter()
