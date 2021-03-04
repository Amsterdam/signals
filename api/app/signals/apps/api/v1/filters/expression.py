# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django_filters.rest_framework import FilterSet, filters

from signals.apps.api.v1.filters.utils import expression_choices, expression_type_choices


class ExpressionFilterSet(FilterSet):
    """
    FilterSet used in the V1 API of expressions, options to filter on:
    - expression name
    - expression type
    """
    name = filters.ChoiceFilter(choices=expression_choices)
    type_name = filters.MultipleChoiceFilter(field_name='_type__name', choices=expression_type_choices)
