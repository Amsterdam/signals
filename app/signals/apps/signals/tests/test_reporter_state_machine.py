# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import pytest
from django.test import TestCase
from django_fsm import TransitionNotAllowed

from signals.apps.signals.factories import ReporterFactory, SignalFactory
from signals.apps.signals.models import Reporter


class TestReporterStateMachine(TestCase):
    EMAIL = 'test@example.com'
    PHONE = '0123456789'

    # transitions to cancelled
    def test_can_transition_from_new_to_cancelled_when_not_original_reporter(self):
        original = ReporterFactory.create(state='approved')
        new = Reporter()
        new._signal = original._signal
        new.save()

        new.cancel()

    def test_cannot_transition_from_new_to_cancelled_when_original_reporter(self):
        new = Reporter()
        new._signal = SignalFactory.create(reporter=new)
        new.save()

        with pytest.raises(TransitionNotAllowed):
            new.cancel()

    # TODO: Test case is questionable, since you can always transition to cancelled, except from approved
    #       or when original reporter
    def test_can_transition_from_new_to_cancelled_when_email_not_included_and_phone_not_changed(self):
        original = ReporterFactory.create(state='approved', phone=self.PHONE)
        new = Reporter()
        new._signal = original._signal
        new.phone = self.PHONE
        new.save()

        new.cancel()

    # TODO: Test case is questionable, since you can always transition to cancelled, except from approved
    #       or when original reporter
    def test_can_transition_from_new_to_cancelled_when_email_not_changed_and_phone_not_changed(self):
        original = ReporterFactory.create(state='approved', email=self.EMAIL, phone=self.PHONE)
        new = Reporter()
        new._signal = original._signal
        new.email = self.EMAIL
        new.phone = self.PHONE
        new.save()

        new.cancel()

    def test_can_transition_from_verification_email_sent_to_cancelled(self):
        original = ReporterFactory.create(state='approved', email=self.EMAIL, phone=self.PHONE)
        new = ReporterFactory.create(state='verification_email_sent', _signal=original._signal)

        new.cancel()

    def test_cannot_transition_from_approved_to_cancelled(self):
        original = ReporterFactory.create(state='approved', email=self.EMAIL, phone=self.PHONE)
        new = ReporterFactory.create(state='approved', _signal=original._signal)

        with pytest.raises(TransitionNotAllowed) as e_info:
            new.cancel()

        self.assertEqual(str(e_info.value), "Can't switch from state 'approved' using method 'cancel'")

    def test_cannot_transition_from_cancelled_to_cancelled(self):
        original = ReporterFactory.create(state='approved', email=self.EMAIL, phone=self.PHONE)
        new = ReporterFactory.create(state='cancelled', _signal=original._signal)

        with pytest.raises(TransitionNotAllowed) as e_info:
            new.cancel()

        self.assertEqual(str(e_info.value), "Can't switch from state 'cancelled' using method 'cancel'")

    # transitions to verification_email_sent
    def test_can_transition_from_new_to_verification_email_sent(self):
        original = ReporterFactory.create(state='approved', email=self.EMAIL, phone=self.PHONE)
        new = Reporter()
        new._signal = original._signal
        new.email = 'new@example.com'
        new.phone = self.PHONE
        new.save()

        new.verify_email()

    def test_cannot_transition_from_new_to_verification_email_sent_when_email_not_changed(self):
        original = ReporterFactory.create(state='approved', email=self.EMAIL, phone=self.PHONE)
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
        reporter = ReporterFactory.create(state='cancelled', email=self.EMAIL, phone=self.PHONE)

        with pytest.raises(TransitionNotAllowed) as e_info:
            reporter.verify_email()

        self.assertEqual(str(e_info.value), "Can't switch from state 'cancelled' using method 'verify_email'")

    def test_cannot_transition_from_approved_to_verification_email_sent(self):
        reporter = ReporterFactory.create(state='approved', email=self.EMAIL, phone=self.PHONE)

        with pytest.raises(TransitionNotAllowed) as e_info:
            reporter.verify_email()

        self.assertEqual(str(e_info.value), "Can't switch from state 'approved' using method 'verify_email'")

    def test_cannot_transition_from_verification_email_sent_to_verification_email_sent(self):
        reporter = ReporterFactory.create(state='verification_email_sent', email=self.EMAIL, phone=self.PHONE)

        with pytest.raises(TransitionNotAllowed) as e_info:
            reporter.verify_email()

        self.assertEqual(
            str(e_info.value),
            "Can't switch from state 'verification_email_sent' using method 'verify_email'"
        )

    # transitions to approved
    def test_can_transition_from_new_to_approved_when_original_reporter(self):
        reporter = Reporter()
        reporter._signal = SignalFactory.create(reporter=None)
        reporter.save()

        reporter.approve()

    def test_can_transition_from_new_to_approved_when_email_not_included_and_phone_number_changed(self):
        original = ReporterFactory.create(state='approved', phone=self.PHONE)
        new = Reporter()
        new._signal = original._signal
        new.phone = '0987654321'
        new.save()

        new.approve()

    def test_cannot_transition_from_new_to_approved_when_email_not_included_and_phone_not_changed(self):
        original = ReporterFactory.create(state='approved', phone=self.PHONE)
        new = Reporter()
        new._signal = original._signal
        new.phone = self.PHONE
        new.save()

        with pytest.raises(TransitionNotAllowed):
            new.approve()

    def test_can_transition_from_new_to_approved_when_email_included_but_not_changed_and_phone_changed(self):
        pass

    def test_cannot_transition_from_new_to_approved_when_email_included_not_changed_and_phone_not_changed(self):
        pass

    def test_can_transition_from_verification_email_sent_to_approved(self):
        pass

    def test_cannot_transition_from_verification_email_sent_to_approved(self):
        pass

    def test_cannot_transition_from_cancelled_to_approved(self):
        pass

    def test_cannot_transition_from_approved_to_approved(self):
        pass
