from django_filters import FilterSet, OrderingFilter, filters

from signals.apps.api.v1.filters import status_choices


class CategoryFilterSet(FilterSet):
    slug = filters.CharFilter(lookup_expr='iexact')

    order_by = OrderingFilter(
        fields=(
            ('slug', 'slug')
        )
    )


class DepartmentFilterSet(FilterSet):
    is_intern = filters.BooleanFilter()

    order_by = OrderingFilter(
        fields=(
            ('code', 'code')
        )
    )


class ServiceLevelObjectiveFilterSet(FilterSet):
    order_by = OrderingFilter(
        fields=(
            ('created_at', 'created_at')
        )
    )


class StatusMessageTemplateFilterSet(FilterSet):
    state = filters.ChoiceFilter(choices=status_choices)

    order_by = OrderingFilter(
        fields=(
            ('order', 'order')
        )
    )
