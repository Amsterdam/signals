# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from pytest_bdd import then, parsers

from signals.apps.signals.models import Signal


@then(parsers.parse('the history should state {statement}'))
def then_history_should_state(statement: str, signal: Signal) -> None:
    history = signal.history_log.all()
    found = False
    for log in history:
        if log.description == statement:
            found = True
            break

    assert found
