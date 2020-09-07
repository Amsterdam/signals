from django.db.models import Count, F, Max, Q
from django_filters.rest_framework import FilterSet, filters

from signals.apps.api.v1.filters.utils import (
    _get_child_category_queryset,
    _get_parent_category_queryset,
    area_choices,
    area_type_choices,
    buurt_choices,
    contact_details_choices,
    department_choices,
    feedback_choices,
    kind_choices,
    source_choices,
    stadsdelen_choices,
    status_choices
)
from signals.apps.signals.models import Category, Priority, Type


class SignalFilter(FilterSet):
    id = filters.NumberFilter()
    address_text = filters.CharFilter(field_name='location__address_text', lookup_expr='icontains')
    area_code = filters.ChoiceFilter(field_name='location__area_code', choices=area_choices)
    area_type_code = filters.ChoiceFilter(field_name='location__area_type_code', choices=area_type_choices)
    buurt_code = filters.MultipleChoiceFilter(field_name='location__buurt_code', choices=buurt_choices)
    category_slug = filters.ModelMultipleChoiceFilter(
        queryset=_get_child_category_queryset(),
        to_field_name='slug',
        field_name='category_assignment__category__slug',
    )
    contact_details = filters.MultipleChoiceFilter(method='contact_details_filter', choices=contact_details_choices)
    created_before = filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='lte')
    created_after = filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='gte')
    directing_department = filters.MultipleChoiceFilter(
        field_name='directing_departments_assignment__departments__code',
        choices=department_choices
    )
    feedback = filters.ChoiceFilter(method='feedback_filter', choices=feedback_choices)
    kind = filters.ChoiceFilter(method='kind_filter', choices=kind_choices)  # SIG-2636
    incident_date = filters.DateFilter(field_name='incident_date_start', lookup_expr='date')
    incident_date_before = filters.DateFilter(field_name='incident_date_start', lookup_expr='date__gte')
    incident_date_after = filters.DateFilter(field_name='incident_date_start', lookup_expr='date__lte')
    maincategory_slug = filters.ModelMultipleChoiceFilter(
        queryset=_get_parent_category_queryset(),
        to_field_name='slug',
        field_name='category_assignment__category__parent__slug',
    )
    note_keyword = filters.CharFilter(method='note_keyword_filter')
    priority = filters.MultipleChoiceFilter(field_name='priority__priority', choices=Priority.PRIORITY_CHOICES)
    source = filters.MultipleChoiceFilter(choices=source_choices)
    stadsdeel = filters.MultipleChoiceFilter(field_name='location__stadsdeel', choices=stadsdelen_choices)
    status = filters.MultipleChoiceFilter(field_name='status__state', choices=status_choices)
    type = filters.MultipleChoiceFilter(method='type_filter', choices=Type.CHOICES)
    updated_before = filters.IsoDateTimeFilter(field_name='updated_at', lookup_expr='lte')
    updated_after = filters.IsoDateTimeFilter(field_name='updated_at', lookup_expr='gte')

    def _cleanup_form_data(self):
        """
        Cleanup the form data
        """
        self.form.cleaned_data.pop('category_slug', None)
        self.form.cleaned_data.pop('maincategory_slug', None)

        if not self.form.cleaned_data.get('area_code', None) or not self.form.cleaned_data.get('area_type_code', None):
            self.form.cleaned_data.pop('area_code', None)
            self.form.cleaned_data.pop('area_type_code', None)

    def filter_queryset(self, queryset):
        """
        Add custom category filtering to the filter_queryset
        """
        main_categories = self.form.cleaned_data['maincategory_slug']
        sub_categories = self.form.cleaned_data['category_slug']

        if main_categories or sub_categories:
            queryset = queryset.filter(
                Q(category_assignment__category__parent_id__in=[c.pk for c in main_categories]) |
                Q(category_assignment__category_id__in=[c.pk for c in sub_categories])
            )

        self._cleanup_form_data()
        return super(SignalFilter, self).filter_queryset(queryset=queryset)

    # Custom filter functions

    def contact_details_filter(self, queryset, name, value):
        """
        Filter `signals.Signal` instances according to presence of contact details.
        """
        choices = value  # we have a MultipleChoiceFilter ...

        # Deal with all choices selected, or none selected:
        if len(choices) == len(contact_details_choices()):
            # No filters are present, or ... all filters are present. In that
            # case we want all Signal instances with an email address, or a
            # phone number, or none of those (according to) the UX design.
            # This is the same as not filtering, hence in both cases just
            # return the queryset.
            return queryset

        # Set-up our Q objects for the individual options.
        has_no_email = (Q(reporter__email__isnull=True) | Q(reporter__email=''))
        has_no_phone = (Q(reporter__phone__isnull=True) | Q(reporter__phone=''))
        is_anonymous = has_no_email & has_no_phone

        q_objects = {
            'email': ~has_no_email,
            'phone': ~has_no_phone,
            'none': is_anonymous,
        }

        # The individual choices have to be combined using logical OR:
        q_total = q_objects[choices.pop()]
        while choices:
            q_total |= q_objects[choices.pop()]

        return queryset.filter(q_total)

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

    def kind_filter(self, queryset, name, value):
        q_objects = {
            'signal': (Q(parent__isnull=True) & Q(children__isnull=True)),
            'parent_signal': (Q(parent__isnull=True) & Q(children__isnull=False)),
            'child_signal': (Q(parent__isnull=False)),
        }
        q_filter = q_objects.get(value.lower(), None)
        return queryset.filter(q_filter).distinct() if q_filter else queryset

    def note_keyword_filter(self, queryset, name, value):
        return queryset.filter(notes__text__icontains=value).distinct()

    def type_filter(self, queryset, name, value):
        return queryset.annotate(type_assignment_id=Max('types__id')).filter(types__id=F('type_assignment_id'),
                                                                             types__name__in=value)


class SignalCategoryRemovedAfterFilter(FilterSet):
    after = filters.IsoDateTimeFilter(field_name='category_assignment__created_at', lookup_expr='gte')
    before = filters.IsoDateTimeFilter(field_name='category_assignment__created_at', lookup_expr='lte')
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
