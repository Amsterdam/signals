from django.contrib.auth.models import Group
from django.db.models.functions import Lower
from django_filters.rest_framework import FilterSet, filters

from signals.apps.api.generics.filters import OrderingExtraKwargsFilter


def _get_group_queryset():
    return Group.objects.all()


class UserFilterSet(FilterSet):
    id = filters.NumberFilter()
    username = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter(field_name='is_active')

    role = filters.ModelMultipleChoiceFilter(queryset=_get_group_queryset(),
                                             to_field_name='name',
                                             field_name='groups__name')

    order = OrderingExtraKwargsFilter(
        fields=(
            ('username', 'username'),
            ('is_active', 'is_active'),
        ),
        extra_kwargs={
            'username': {'apply': Lower}  # Will apply the Lower function when ordering
        }
    )
