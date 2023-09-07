# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from pytest_bdd import parsers, when

from signals.apps.signals.tasks import delete_signals_in_state_for_x_days
from signals.apps.signals.tests.scenarios.context.utils import get_state_code, nr_of_days_in_years


@when(
    parsers.parse('the system runs the task to delete Signals in {state} for more than {years:d} years'),
    target_fixture='response',
)
def when_the_system_runs_task_to_delete_signals(state: str, years: int):
    days = nr_of_days_in_years(years)
    state = get_state_code(state)

    delete_signals_in_state_for_x_days(state=state, days=days)
