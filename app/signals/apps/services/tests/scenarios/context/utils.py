# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import calendar

from django.utils import timezone

from signals.apps.signals.workflow import STATUS_CHOICES


def get_state_code(human_readable_state: str) -> str:
    human_readable_state = human_readable_state.lower()
    choices = dict(STATUS_CHOICES)
    for key, value in choices.items():
        if value.lower() == human_readable_state:
            return key
    return human_readable_state


def nr_of_days_in_years(years: int) -> int:
    now = timezone.now()
    return sum(
        366 if calendar.isleap(year) else 365
        for year in range(now.year, now.year + years)
    )
