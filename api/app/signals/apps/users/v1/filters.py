from django.contrib.auth.models import Group
from django_filters.rest_framework import FilterSet, filters


def _get_group_queryset():
    return Group.objects.all()


class UserFilter(FilterSet):
    id = filters.NumberFilter()
    username = filters.CharFilter(lookup_expr='icontains')
    active = filters.BooleanFilter(field_name='is_active')

    role = filters.ModelMultipleChoiceFilter(queryset=_get_group_queryset(),
                                             to_field_name='name',
                                             field_name='groups__name')
