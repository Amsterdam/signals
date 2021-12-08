# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.conf import settings
from django.db.models import Q
from django.utils.timezone import now
from django_filters.rest_framework import FilterSet, filters

from signals.apps.api.filters.utils import (
    _get_child_category_queryset,
    _get_parent_category_queryset,
    area_choices,
    area_type_choices,
    boolean_choices,
    buurt_choices,
    category_choices,
    contact_details_choices,
    department_choices,
    feedback_choices,
    kind_choices,
    punctuality_choices,
    source_choices,
    stadsdelen_choices,
    status_choices
)
from signals.apps.signals import workflow
from signals.apps.signals.models import Note, Priority, Type


class SignalFilterSet(FilterSet):
    id = filters.NumberFilter(field_name='signal_id')
    address_text = filters.CharFilter(field_name='location_address_text', lookup_expr='icontains')
    area_code = filters.MultipleChoiceFilter(field_name='location_area_code', choices=area_choices)
    area_type_code = filters.ChoiceFilter(field_name='location_area_code_type', choices=area_type_choices)
    buurt_code = filters.MultipleChoiceFilter(field_name='location_buurt_code', choices=buurt_choices)
    category_id = filters.MultipleChoiceFilter(field_name='child_category_id', choices=category_choices)
    category_slug = filters.ModelMultipleChoiceFilter(queryset=_get_child_category_queryset(), to_field_name='slug',
                                                      field_name='child_category_slug')
    contact_details = filters.MultipleChoiceFilter(method='contact_details_filter', choices=contact_details_choices)
    created_after = filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='lte')
    directing_department = filters.MultipleChoiceFilter(method='directing_department_filter',
                                                        choices=department_choices)
    feedback = filters.ChoiceFilter(method='feedback_filter', choices=feedback_choices)
    has_changed_children = filters.MultipleChoiceFilter(method='has_changed_children_filter', choices=boolean_choices)
    kind = filters.MultipleChoiceFilter(method='kind_filter', choices=kind_choices)
    incident_date = filters.DateFilter(field_name='incident_date_start', lookup_expr='date')
    incident_date_before = filters.DateFilter(field_name='incident_date_start', lookup_expr='date__gte')
    incident_date_after = filters.DateFilter(field_name='incident_date_start', lookup_expr='date__lte')
    maincategory_slug = filters.ModelMultipleChoiceFilter(queryset=_get_parent_category_queryset(),
                                                          to_field_name='slug', field_name='parent_category_slug')
    note_keyword = filters.CharFilter(method='note_keyword_filter')
    priority = filters.MultipleChoiceFilter(field_name='priority_priority', choices=Priority.PRIORITY_CHOICES)
    source = filters.MultipleChoiceFilter(choices=source_choices)
    stadsdeel = filters.MultipleChoiceFilter(field_name='location_stadsdeel', choices=stadsdelen_choices)
    status = filters.MultipleChoiceFilter(field_name='status_state', choices=status_choices)
    type = filters.MultipleChoiceFilter(field_name='type_name', choices=Type.CHOICES)
    updated_before = filters.IsoDateTimeFilter(field_name='updated_at', lookup_expr='lte')
    updated_after = filters.IsoDateTimeFilter(field_name='updated_at', lookup_expr='gte')
    assigned_user_email = filters.CharFilter(method='assigned_user_email_filter')
    reporter_email = filters.CharFilter(field_name='reporter_email', lookup_expr='iexact')
    routing_department_code = filters.MultipleChoiceFilter(field_name='routing_assignment__departments__code',
                                                           choices=department_choices)
    punctuality = filters.ChoiceFilter(method='punctuality_filter', choices=punctuality_choices)

    def _cleanup_form_data(self):
        """
        Cleanup the form data
        """
        self.form.cleaned_data.pop('category_slug', None)
        self.form.cleaned_data.pop('maincategory_slug', None)

    def filter_queryset(self, queryset):
        """
        Add custom category filtering to the filter_queryset
        """
        if not self.form.cleaned_data['category_id']:
            main_categories = self.form.cleaned_data['maincategory_slug']
            sub_categories = self.form.cleaned_data['category_slug']

            if main_categories or sub_categories:
                queryset = queryset.filter(
                    Q(parent_category_id__in=[c.pk for c in main_categories]) |
                    Q(child_category_id__in=[c.pk for c in sub_categories])
                )

        self._cleanup_form_data()
        queryset = super().filter_queryset(queryset=queryset)
        return queryset

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
        has_no_email = (Q(reporter_email__isnull=True) | Q(reporter_email=''))
        has_no_phone = (Q(reporter_phone__isnull=True) | Q(reporter_phone=''))
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

    def has_changed_children_filter(self, queryset, name, value):
        choices = set(map(lambda x: True if x in settings.TRUE_VALUES else False, value))
        q_filter = Q(is_parent=True)
        if len(choices) == 2:
            return queryset.filter(q_filter)

        if True in choices:
            q_filter &= Q(has_changed_children=True)

        if False in choices:
            q_filter &= Q(has_changed_children=False)

        return queryset.filter(q_filter).distinct()

    def feedback_filter(self, queryset, name, value):
        # Only signals that have feedback
        if value in ['satisfied', 'not_satisfied']:
            is_satisfied = True if value == 'satisfied' else False
            queryset = queryset.filter(feedback_is_satisfied=is_satisfied, feedback_created_at__isnull=False,
                                       feedback_submitted_at__isnull=False)
        elif value == 'not_received':
            queryset = queryset.filter(feedback_created_at__isnull=False, feedback_submitted_at__isnull=True)

        return queryset

    def kind_filter(self, queryset, name, value):
        choices = value  # we have a MultipleChoiceFilter ...

        if (len(choices) == len(kind_choices())
                or {'signal', 'parent_signal', 'child_signal'} == set(choices)
                or {'parent_signal', 'exclude_parent_signal'} == set(choices)):
            return queryset

        q_objects = {
            'signal': (Q(is_signal=True) & Q(is_parent=False) & Q(is_child=False)),
            'parent_signal': (Q(is_signal=False) & Q(is_parent=True) & Q(is_child=False)),
            'exclude_parent_signal': ~(Q(is_parent=True) & Q(is_child=False)),
            'child_signal': (Q(is_signal=False) & Q(is_parent=False) & Q(is_child=True)),
        }

        q_filter = q_objects[choices.pop()]
        while choices:
            q_filter |= q_objects[choices.pop()]

        return queryset.filter(q_filter) if q_filter else queryset

    def note_keyword_filter(self, queryset, name, value):
        return queryset.filter(signal_id__in=Note.objects.filter(text__icontains=value).values_list('_signal_id'))

    def punctuality_filter(self, queryset, name, value):
        # When work on a Signal was finished, it can no longer be late and it is excluded.
        queryset = queryset.exclude(status_state__in=[workflow.AFGEHANDELD, workflow.GEANNULEERD, workflow.GESPLITST])

        # Historical data will not have deadlines calculated for it and can be
        # filtered for by using this filter's "null" option.
        if value == 'null':
            return queryset.filter(category_assignment_deadline__isnull=True)

        # Not interested in historical data without deadlines:
        queryset = queryset.exclude(category_assignment_deadline__isnull=True)

        local_now = now()
        if value == 'on_time':
            return queryset.filter(category_assignment_deadline__gt=local_now)
        elif value == 'late':
            return queryset.filter(category_assignment_deadline__lt=local_now)
        elif value == 'late_factor_3':
            return queryset.filter(category_assignment_deadline_factor_3__lt=local_now)

    def directing_department_filter(self, queryset, name, value):
        """
        Filter Signals on directing department.

        * A directing department can only be set on a Parent Signal
        * When providing the option "null" select all parent Signals without one or more directing departments
        * When providing on or more department codes as options select all parent Signals which match directing
          departments

        Example 1: "?directing_department=ASC" will select all parent Signals where ASC is the directing department
        Example 2: "?directing_department=ASC&directing_department=null" will select all parent Signals without a
                   directing department OR ASC as the directing department
        Example 3: "?directing_department=null" will select all parent Signals without a directing department
        """
        choices = value  # we have a MultipleChoiceFilter ...
        if len(choices) == len(department_choices()):
            # No filters are present, or ... all filters are present. In that case we want all Signal instances
            return queryset

        # Directing departments are only set on parent Signals
        parent_q_filter = (Q(is_parent=True) & Q(is_child=False))

        if 'null' in choices and len(choices) == 1:
            # "?directing_department=null" will select all parent Signals without a directing department
            return queryset.filter(
                parent_q_filter &
                (
                    Q(directing_departments_assignment__isnull=True) |
                    Q(directing_departments_assignment__departments__isnull=True)
                )
            ).distinct()
        elif 'null' in choices and len(choices) > 1:
            # "?directing_department=ASC&directing_department=null" will select all parent Signals without a directing
            # department OR ASC as the directing department
            choices.pop(choices.index('null'))
            return queryset.filter(
                parent_q_filter & (
                    Q(directing_departments_assignment__isnull=True) |
                    Q(directing_departments_assignment__departments__isnull=True) |
                    Q(directing_departments_assignment__departments__code__in=choices)
                )
            ).distinct()
        elif len(choices):
            # "?directing_department=ASC" will select all parent Signals where ASC is the directing department
            return queryset.filter(
                parent_q_filter &
                Q(directing_departments_assignment__departments__code__in=choices)
            ).distinct()
        return queryset

    def assigned_user_email_filter(self, queryset, name, value):
        if value == 'null':
            return queryset.filter(assigned_user_email__isnull=True)
        else:
            return queryset.filter(assigned_user_email__iexact=value)
