# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from django_filters.rest_framework import FilterSet, filters


class DepartmentFilterSet(FilterSet):
    can_direct = filters.BooleanFilter()
