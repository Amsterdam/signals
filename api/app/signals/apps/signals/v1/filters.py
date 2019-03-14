from django_filters.rest_framework import FilterSet, filters

from signals.apps.signals.api_generics.filters import IntegerFilter, status_choices
from signals.apps.signals.models import Category, MainCategory


class SignalFilter(FilterSet):
    id = IntegerFilter()

    created_before = filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='lte')
    created_after = filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='gte')

    updated_before = filters.IsoDateTimeFilter(field_name='updated_at', lookup_expr='lte')
    updated_after = filters.IsoDateTimeFilter(field_name='updated_at', lookup_expr='gte')

    status = filters.MultipleChoiceFilter(field_name='status__state', choices=status_choices)

    maincategory_slug = filters.ModelMultipleChoiceFilter(
        queryset=MainCategory.objects.all(),
        to_field_name='slug',
        field_name='category_assignment__category__main_category__slug',
    )

    # category_slug, because we will soon be using one type of category, instead of main vs sub
    # categories. This way the naming in the API will remain consistent
    category_slug = filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.all(),
        to_field_name='slug',
        field_name='category_assignment__category__slug',
    )
