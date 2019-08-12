from django.db.models import Count, F, Max, Q
from django_filters.rest_framework import FilterSet, filters

from signals.apps.api.generics.filters import buurt_choices, status_choices
from signals.apps.signals.models import STADSDELEN, Category, Priority

feedback_choices = (
    ('satisfied', 'satisfied'),
    ('not_satisfied', 'not_satisfied'),
    ('not_received', 'not_received'),
)


class SignalFilter(FilterSet):
    id = filters.NumberFilter()

    created_before = filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='lte')
    created_after = filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='gte')

    updated_before = filters.IsoDateTimeFilter(field_name='updated_at', lookup_expr='lte')
    updated_after = filters.IsoDateTimeFilter(field_name='updated_at', lookup_expr='gte')

    status = filters.MultipleChoiceFilter(field_name='status__state', choices=status_choices)

    maincategory_slug = filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.filter(parent__isnull=True),
        to_field_name='slug',
        field_name='category_assignment__category__parent__slug',
    )

    # category_slug, because we will soon be using one type of category, instead of main vs sub
    # categories. This way the naming in the API will remain consistent
    category_slug = filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.all(),
        to_field_name='slug',
        field_name='category_assignment__category__slug',
    )

    priority = filters.ChoiceFilter(field_name='priority__priority',
                                    choices=Priority.PRIORITY_CHOICES)

    stadsdeel = filters.MultipleChoiceFilter(field_name='location__stadsdeel',
                                             choices=STADSDELEN)
    buurt_code = filters.MultipleChoiceFilter(field_name='location__buurt_code',
                                              choices=buurt_choices)
    address_text = filters.CharFilter(field_name='location__address_text',
                                      lookup_expr='icontains')

    incident_date = filters.DateFilter(field_name='incident_date_start', lookup_expr='date')
    incident_date_before = filters.DateFilter(field_name='incident_date_start',
                                              lookup_expr='date__gte')
    incident_date_after = filters.DateFilter(field_name='incident_date_start',
                                             lookup_expr='date__lte')

    feedback = filters.ChoiceFilter(method='feedback_filter', choices=feedback_choices)

    def feedback_filter(self, queryset, name, value):
        # Only signals that have feedback
        queryset = queryset.annotate(feedback_count=Count('feedback')).filter(feedback_count__gte=1)

        if value in ['satisfied', 'not_satisfied']:
            is_satisfied = True if value == 'satisfied' else False
            queryset = queryset.annotate(
                feedback_max_created_at=Max('feedback__created_at'),
                feedback_max_submitted_at=Max('feedback__submitted_at')
            ).filter(
                feedback__is_satisfied=is_satisfied,
                feedback__submitted_at__isnull=False,
                feedback__created_at=F('feedback_max_created_at'),
                feedback__submitted_at=F('feedback_max_submitted_at')
            )
        elif value == 'not_received':
            queryset = queryset.annotate(
                feedback_max_created_at=Max('feedback__created_at')
            ).filter(
                feedback__submitted_at__isnull=True,
                feedback__created_at=F('feedback_max_created_at')
            )

        return queryset


class SignalCategoryRemovedAfterFilter(FilterSet):
    before = filters.IsoDateTimeFilter(field_name='category_assignment__created_at',
                                       lookup_expr='lte')

    after = filters.IsoDateTimeFilter(field_name='category_assignment__created_at',
                                      lookup_expr='gte')

    category_slug = filters.ModelMultipleChoiceFilter(
        method='category_filter',
        queryset=Category.objects.all(),
        to_field_name='slug',
        field_name='category_assignment__category__slug',
    )

    def category_filter(self, queryset, name, value):
        # TODO: Get categories from user permissions, can be added after PR
        #       https://github.com/Amsterdam/signals/pull/202 has been approved and merged

        if len(value):
            # We need to check the given categories
            categories_to_check = [v.id for v in value]
        else:
            # A list of category id's that the currently logged in user has permissions for
            categories_to_check = Category.objects.all().values_list('id', flat=True)

        return queryset.filter(
            Q(category_assignment__isnull=False) &
            Q(categories__id__in=categories_to_check) &
            ~Q(category_assignment__category_id__in=categories_to_check)
        )
