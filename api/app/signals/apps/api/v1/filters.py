from django.db.models import Count, F, Max, Q
from django_filters.rest_framework import FilterSet, filters

from signals.apps.api.generics.filters import buurt_choices, status_choices
from signals.apps.signals.models import STADSDELEN, Category, Priority, Signal, Type

feedback_choices = (
    ('satisfied', 'satisfied'),
    ('not_satisfied', 'not_satisfied'),
    ('not_received', 'not_received'),
)

contact_details_choices = (
    ('none', 'none'),
    ('email', 'email'),
    ('phone', 'phone')
)


def _get_child_category_queryset():
    return Category.objects.filter(parent__isnull=False)


def _get_parent_category_queryset():
    return Category.objects.filter(parent__isnull=True)


def source_choices():
    choices = Signal.objects.order_by('source').values_list('source', flat=True).distinct()
    return [(choice, f'{choice}') for choice in choices]


def stadsdelen():
    """
    Returns all available choices for stadsdelen

    SIG-1938 Added 'null' so that the filter can also filter on signals with a stadsdeel with the
    value null in the database
    """
    return (
        ('null', 'Niet bepaald'),
    ) + STADSDELEN


class SignalFilter(FilterSet):
    id = filters.NumberFilter()

    created_before = filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='lte')
    created_after = filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='gte')

    updated_before = filters.IsoDateTimeFilter(field_name='updated_at', lookup_expr='lte')
    updated_after = filters.IsoDateTimeFilter(field_name='updated_at', lookup_expr='gte')

    status = filters.MultipleChoiceFilter(field_name='status__state', choices=status_choices)

    maincategory_slug = filters.ModelMultipleChoiceFilter(
        queryset=_get_parent_category_queryset(),
        to_field_name='slug',
        field_name='category_assignment__category__parent__slug',
    )

    # category_slug, because we will soon be using one type of category, instead of main vs sub
    # categories. This way the naming in the API will remain consistent
    category_slug = filters.ModelMultipleChoiceFilter(
        queryset=_get_child_category_queryset(),
        to_field_name='slug',
        field_name='category_assignment__category__slug',
    )

    priority = filters.MultipleChoiceFilter(field_name='priority__priority',
                                            choices=Priority.PRIORITY_CHOICES)

    stadsdeel = filters.MultipleChoiceFilter(field_name='location__stadsdeel',
                                             choices=stadsdelen)
    buurt_code = filters.MultipleChoiceFilter(field_name='location__buurt_code',
                                              choices=buurt_choices)
    address_text = filters.CharFilter(field_name='location__address_text',
                                      lookup_expr='icontains')

    incident_date = filters.DateFilter(field_name='incident_date_start', lookup_expr='date')
    incident_date_before = filters.DateFilter(field_name='incident_date_start',
                                              lookup_expr='date__gte')
    incident_date_after = filters.DateFilter(field_name='incident_date_start',
                                             lookup_expr='date__lte')

    source = filters.MultipleChoiceFilter(choices=source_choices)

    feedback = filters.ChoiceFilter(method='feedback_filter', choices=feedback_choices)

    contact_details = filters.MultipleChoiceFilter(
        method='contact_details_filter',
        choices=contact_details_choices,
    )

    # SIG-2148 Filter on Signal Type
    type = filters.MultipleChoiceFilter(method='type_filter', choices=Type.CHOICES)

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

    def _categories_filter(self, queryset, main_categories, sub_categories):
        if not main_categories and not sub_categories:
            return queryset

        queryset = queryset.filter(
            Q(category_assignment__category__parent_id__in=[c.pk for c in main_categories]) |
            Q(category_assignment__category_id__in=[c.pk for c in sub_categories])
        )
        return queryset

    def filter_queryset(self, queryset):
        main_categories = []
        sub_categories = []

        for name, value in self.form.cleaned_data.items():
            if name.lower() == 'maincategory_slug':
                main_categories = value
            elif name.lower() == 'category_slug':
                sub_categories = value
            else:
                queryset = self.filters[name].filter(queryset, value)

        return self._categories_filter(queryset=queryset,
                                       main_categories=main_categories,
                                       sub_categories=sub_categories)

    def contact_details_filter(self, queryset, name, value):
        """
        Filter `signals.Signal` instances according to presence of contact details.
        """
        # Set-up our Q objects for the individual options.
        has_no_email = (Q(reporter__email__isnull=True) | Q(reporter__email=''))
        has_no_phone = (Q(reporter__phone__isnull=True) | Q(reporter__phone=''))
        is_anonymous = has_no_email & has_no_phone

        q_objects = {
            'email': ~has_no_email,
            'phone': ~has_no_phone,
            'none': is_anonymous,
        }

        choices = value  # we have a MultipleChoiceFilter ...

        # Deal with all choices selected, or none selected:
        if len(choices) == len(contact_details_choices):
            # No filters are present, or ... all filters are present. In that
            # case we want all Signal instances with an email address, or a
            # phone number, or none of those (according to) the UX design.
            # This is the same as not filtering, hence in both cases just
            # return the queryset.
            return queryset

        # The individual choices have to be combined using logical OR:
        q_total = q_objects[choices.pop()]
        while choices:
            q_total |= q_objects[choices.pop()]

        return queryset.filter(q_total)

    def type_filter(self, queryset, name, value):
        return queryset.annotate(
            type_assignment_id=Max('types__id')
        ).filter(
            types__id=F('type_assignment_id'),
            types__name__in=value
        )


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
