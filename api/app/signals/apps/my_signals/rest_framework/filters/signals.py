# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django_filters.rest_framework import FilterSet, filters

from signals.apps.signals.workflow import AFGEHANDELD, GEANNULEERD, GESPLITST


class MySignalFilterSet(FilterSet):
    status = filters.ChoiceFilter(method='filter_status', field_name='status__state',
                                  choices=[('open', 'Open'), ('closed', 'Closed')])

    def filter_status(self, queryset, name, value):
        filter_kwargs = {f'{name}__in': [AFGEHANDELD, GEANNULEERD, GESPLITST, ]}
        if value.lower() == 'open':
            # Only Signals in a "closed" state will be returned
            return queryset.exclude(**filter_kwargs)
        else:
            # Only Signals in an "open" state will be returned
            return queryset.filter(**filter_kwargs)
