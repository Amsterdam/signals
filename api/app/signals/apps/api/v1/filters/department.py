from django_filters.rest_framework import FilterSet, filters


class DepartmentFilterSet(FilterSet):
    can_direct = filters.BooleanFilter()
