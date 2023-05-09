# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django_filters.rest_framework import FilterSet, filters

from signals.apps.api.filters import category_choices, status_choices


class StatusMessagesFilterSet(FilterSet):
    active = filters.BooleanFilter()
    category_id = filters.MultipleChoiceFilter(field_name='categories', choices=category_choices)
    state = filters.MultipleChoiceFilter(choices=status_choices)
