# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from pytest_bdd import given, parsers

from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Reporter, Signal


@given(
    parsers.parse('there is a signal with reporter phone number {phone} and email address {email}'),
    target_fixture='signal',
)
def given_signal_reporter(phone: str, email: str) -> Signal:
    return SignalFactory.create(
        reporter__phone=phone,
        reporter__email=email,
        reporter__state=Reporter.REPORTER_STATE_APPROVED
    )
