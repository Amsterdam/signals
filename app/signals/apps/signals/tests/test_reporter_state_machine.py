# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import typing

import pytest
from django.test import TestCase
from django_fsm import TransitionNotAllowed

from signals.apps.email_integrations.factories import EmailTemplateFactory
from signals.apps.email_integrations.models import EmailTemplate
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
        new.save()

        self.assertEqual(new.state, Reporter.REPORTER_STATE_CANCELLED)

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
        new.save()

        self.assertEqual(new.state, Reporter.REPORTER_STATE_CANCELLED)
        self.assertIsNone(new.email_verification_token)

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

    # transitions to verification_email_sent
    def test_can_transition_from_new_to_verification_email_sent(self):
        EmailTemplateFactory.create(key=EmailTemplate.VERIFY_EMAIL_REPORTER)
        original = ReporterFactory.create(state=Reporter.REPORTER_STATE_APPROVED, email=self.EMAIL, phone=self.PHONE)
        new = Reporter()
        new._signal = original._signal
        new.email = 'new@example.com'
        new.phone = self.PHONE
        new.save()

        new.verify_email()

        self.assertIsNotNone(new.email_verification_token)
        self.assertIsNotNone(new.email_verification_token_expires)
        self.assertFalse(new.email_verified)

    def test_cannot_transition_from_new_to_verification_email_sent_when_email_not_changed(self):
        original = ReporterFactory.create(state=Reporter.REPORTER_STATE_APPROVED, email=self.EMAIL, phone=self.PHONE)
        new = Reporter()
        new._signal = original._signal
        new.email = self.EMAIL
        new.phone = self.PHONE
        new.save()

        with pytest.raises(TransitionNotAllowed):
            new.verify_email()

    def test_cannot_transition_from_new_to_verification_email_sent_when_original_reporter(self):
        new = Reporter()
        new._signal = SignalFactory.create(reporter=None)
        new.email = self.EMAIL
        new.phone = self.PHONE
        new.save()

        with pytest.raises(TransitionNotAllowed):
            new.verify_email()

    def test_cannot_transition_from_cancelled_to_verification_email_sent(self):
        reporter = ReporterFactory.create(state=Reporter.REPORTER_STATE_CANCELLED, email=self.EMAIL, phone=self.PHONE)

        with pytest.raises(TransitionNotAllowed) as e_info:
            reporter.verify_email()

        self.assertEqual(str(e_info.value), "Can't switch from state 'cancelled' using method 'verify_email'")

    def test_cannot_transition_from_approved_to_verification_email_sent(self):
        reporter = ReporterFactory.create(state=Reporter.REPORTER_STATE_APPROVED, email=self.EMAIL, phone=self.PHONE)

        with pytest.raises(TransitionNotAllowed) as e_info:
            reporter.verify_email()

        self.assertEqual(str(e_info.value), "Can't switch from state 'approved' using method 'verify_email'")

    def test_cannot_transition_from_verification_email_sent_to_verification_email_sent(self):
        reporter = ReporterFactory.create(
            state=Reporter.REPORTER_STATE_VERIFICATION_EMAIL_SENT,
            email=self.EMAIL,
            phone=self.PHONE
        )

        with pytest.raises(TransitionNotAllowed) as e_info:
            reporter.verify_email()

        self.assertEqual(
            str(e_info.value),
            "Can't switch from state 'verification_email_sent' using method 'verify_email'"
        )
