# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import typing

import pytest
from django.test import TestCase
from django_fsm import TransitionNotAllowed

from signals.apps.signals.factories import ReporterFactory, SignalFactory
from signals.apps.signals.models import Reporter


class TestReporterStateMachine(TestCase):
    EMAIL: typing.Final[str] = 'test@example.com'
    PHONE: typing.Final[str] = '0123456789'

    # transitions to cancelled
    def test_can_transition_from_new_to_cancelled_when_not_original_reporter(self) -> None:
        original = ReporterFactory.create(state=Reporter.REPORTER_STATE_APPROVED)
        new = Reporter()
        new._signal = original._signal
        new.save()

        new.cancel()

    def test_cannot_transition_from_new_to_cancelled_when_original_reporter(self) -> None:
        new = Reporter()
        new._signal = SignalFactory.create(reporter=new)
        new.save()

        with pytest.raises(TransitionNotAllowed):
            new.cancel()


    def test_can_transition_from_verification_email_sent_to_cancelled(self) -> None:
        original = ReporterFactory.create(state=Reporter.REPORTER_STATE_APPROVED, email=self.EMAIL, phone=self.PHONE)
        new = ReporterFactory.create(state=Reporter.REPORTER_STATE_VERIFICATION_EMAIL_SENT, _signal=original._signal)

        new.cancel()

    def test_cannot_transition_from_approved_to_cancelled(self) -> None:
        original = ReporterFactory.create(state=Reporter.REPORTER_STATE_APPROVED, email=self.EMAIL, phone=self.PHONE)
        new = ReporterFactory.create(state=Reporter.REPORTER_STATE_APPROVED, _signal=original._signal)

        with pytest.raises(TransitionNotAllowed) as e_info:
            new.cancel()

        self.assertEqual(str(e_info.value), "Can't switch from state 'approved' using method 'cancel'")

    def test_cannot_transition_from_cancelled_to_cancelled(self) -> None:
        original = ReporterFactory.create(state=Reporter.REPORTER_STATE_APPROVED, email=self.EMAIL, phone=self.PHONE)
        new = ReporterFactory.create(state=Reporter.REPORTER_STATE_CANCELLED, _signal=original._signal)

        with pytest.raises(TransitionNotAllowed) as e_info:
            new.cancel()

        self.assertEqual(str(e_info.value), "Can't switch from state 'cancelled' using method 'cancel'")
