# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django_filters import ChoiceFilter
from django_filters.rest_framework import FilterSet

from signals.apps.signals.models import Reporter


class ReporterFilterSet(FilterSet):
    state = ChoiceFilter(choices=Reporter.REPORTER_STATES, required=False)
