# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from datetime import timedelta

import freezegun
from django.utils import timezone
from pytest_bdd import given, parsers, then

from signals.apps.signals.factories import SignalFactory, StatusFactory
from signals.apps.signals.models import Signal
from signals.apps.signals.tests.scenarios.context.utils import get_state_code, nr_of_days_in_years


@given(
    parsers.parse('a Signal exists in the state {state} and the state has been '
                  'set {years:d} years ago'),
    target_fixture='signal',
)
def given_a_signal_exists_in_state_for_x_years(state: str,
                                               years: int) -> Signal:
    days = nr_of_days_in_years(years)

    now = timezone.now()
    with freezegun.freeze_time(now - timedelta(days=days-1)):
        signal = SignalFactory.create()

    with freezegun.freeze_time(now - timedelta(days=days)):
        status = StatusFactory.create(
            state=get_state_code(state),
            _signal=signal
        )
        signal.status = status
        signal.save()

    signal.refresh_from_db()

    return signal


@then(parsers.parse('the signal should have been deleted'))
def then_signal_deleted(signal: Signal) -> None:
    signal_qs = Signal.objects.filter(id=signal.id)
    assert signal_qs.exists() is False


@then(parsers.parse('the signal should not have been deleted'))
def then_signal_not_deleted(signal: Signal) -> None:
    signal_qs = Signal.objects.filter(id=signal.id)
    assert signal_qs.exists() is True


@given(
    parsers.parse('{nr_of_signals:d} Signals exists in the state {state} and'
                  ' the state has been set {years:d} years ago'),
    target_fixture='signals',
)
def given_x_signals_exists_in_state_for_x_years(nr_of_signals: int,
                                                state: str,
                                                years: int) -> list[Signal]:
    days = nr_of_days_in_years(years)

    signals = []
    for _ in range(nr_of_signals):
        now = timezone.now()
        with freezegun.freeze_time(now - timedelta(days=days-1)):
            signal = SignalFactory.create()

        with freezegun.freeze_time(now - timedelta(days=days)):
            status = StatusFactory.create(
                state=get_state_code(state),
                _signal=signal
            )
            signal.status = status
            signal.save()

        signal.refresh_from_db()
        signals.append(signal)

    return signals


@then(parsers.parse('the signals should have been deleted'))
def then_signals_deleted(signals: list[Signal]) -> None:
    signal_qs = Signal.objects.filter(id__in=[signal.id for signal in signals])
    assert signal_qs.exists() is False


@then(parsers.parse('the signals should not have been deleted'))
def then_signals_not_deleted(signals: list[Signal]) -> None:
    signal_qs = Signal.objects.filter(id__in=[signal.id for signal in signals])
    assert signal_qs.exists() is True
