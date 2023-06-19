# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import pytest
from django.test import TestCase
from django_fsm import TransitionNotAllowed

from signals.apps.signals.factories import ReporterFactory
from signals.apps.signals.models import Reporter


class TestReporterStateMachine(TestCase):
    # transitions to cancelled
    def test_can_transition_from_new_to_cancelled_when_not_original_reporter(self):
        original = ReporterFactory.create(state='approved')
        new = Reporter()
        new._signal = original._signal
        new.save()

        new.cancel()

    def test_cannot_transition_from_new_to_cancelled_when_original_reporter(self):
        pass

    def test_can_transition_from_new_to_cancelled_when_email_not_included_and_phone_not_changed(self):
        # should not be original reporter
        pass

    def test_can_transition_from_new_to_cancelled_when_email_not_changed_and_phone_not_changed(self):
        # should not be original reporter
        pass

    def test_can_transition_from_verification_email_sent_to_cancelled(self):
        pass

    def test_cannot_transition_from_approved_to_cancelled(self):
        pass

    # transitions to verification_email_sent
    def test_can_transition_from_new_to_verification_email_sent(self):
        pass

    def test_cannot_transition_from_new_to_verification_email_sent_when_email_not_changed(self):
        pass

    def test_cannot_transition_from_new_to_verification_email_sent_when_original_reporter(self):
        pass

    def test_cannot_transition_from_cancelled_to_verification_email_sent(self):
        pass

    def test_cannot_transition_from_approved_to_verification_email_sent(self):
        pass

    # transitions to approved
    def test_can_transition_from_new_to_approved_when_original_reporter(self):
        pass

    def test_can_transition_from_new_to_approved_when_email_not_included_and_phone_number_changed(self):
        pass

    def test_cannot_transition_from_new_to_approved_when_email_not_included_and_phone_not_changed(self):
        pass

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
