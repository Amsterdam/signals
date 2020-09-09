from django_filters.rest_framework import FilterSet, filters

from signals.apps.api.v1.filters.utils import area_code_choices, area_type_code_choices


class AreaFilterSet(FilterSet):
    """
    FilterSet used in the V1 API of areas, options to filter on:
    - code
    - type_code
    """
    code = filters.MultipleChoiceFilter(choices=area_code_choices)
    type_code = filters.MultipleChoiceFilter(field_name='_type__code', choices=area_type_code_choices)
