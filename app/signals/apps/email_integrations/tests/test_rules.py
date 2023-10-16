# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from factory.fuzzy import FuzzyText
from freezegun import freeze_time

from signals.apps.email_integrations.rules import (
    ForwardToExternalRule,
    SignalCreatedRule,
    SignalHandledNegativeRule,
    SignalHandledRule,
    SignalOptionalRule,
    SignalReactionRequestReceivedRule,
    SignalReactionRequestRule,
    SignalReopenedRule,
    SignalScheduledRule
)
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.questionnaires.app_settings import NO_REACTION_RECEIVED_TEXT
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory


class RuleTestMixin:
    rule: AbstractRule
    state: str
    send_email = False

    def test_happy_flow(self):
        status_text = FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='test@example.com')
        self.assertTrue(self.rule(signal))

    def test_anonymous_reporter(self):
        status_text = FuzzyText(length=400)

        signal = SignalFactory.create(status__state=self.state, status__text=status_text, reporter__email='')
        self.assertFalse(self.rule(signal))

        signal = SignalFactory.create(status__state=self.state, status__text=status_text, reporter__email=None)
        self.assertFalse(self.rule(signal))

    def test_apply_for_parent_signals(self):
        status_text = FuzzyText(length=400)

        parent_signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                             status__send_email=self.send_email, reporter__email='test@example.com')
        SignalFactory.create(status__state=self.state, status__text=status_text, reporter__email='test@example.com',
                             parent=parent_signal)

        self.assertTrue(self.rule(parent_signal))

    def test_do_not_apply_for_child_signals(self):
        status_text = FuzzyText(length=400)

        parent_signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                             reporter__email='test@example.com')
        child_signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                            reporter__email='test@example.com', parent=parent_signal)

        self.assertFalse(self.rule(child_signal))

    def test_invalid_states(self):
        states = [s[0] for s in workflow.STATUS_CHOICES if s[0] != self.state]
        for state in states:
            signal = SignalFactory.create(status__state=state, reporter__email='test@example.com')
            self.assertFalse(self.rule(signal))


class TestSignalCreatedRule(RuleTestMixin, TestCase):
    """
    Test the SignalCreatedRule. The rule should only be triggerd when the following rules apply:

    - The status is GEMELD
    - The status GEMELD is set only once
    """
    rule = SignalCreatedRule()
    state = workflow.GEMELD

    def test_signal_set_state_second_time(self):
        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com')

        status = StatusFactory.create(_signal=signal, state=workflow.BEHANDELING)
        signal.status = status
        signal.save()

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertFalse(self.rule(signal))

    def test_signal_set_state_multiple_times(self):
        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com')

        for x in range(5):
            with freeze_time(timezone.now() + timedelta(hours=x)):
                status = StatusFactory.create(_signal=signal, state=self.state)
                signal.status = status
                signal.save()

        self.assertFalse(self.rule(signal))


class TestSignalHandledRule(RuleTestMixin, TestCase):
    """
    Test the SignalHandledRule. The rule should only be triggerd when the following rules apply:

    - The status is AFGEHANDELD
    - The previous state is not VERZOEK_TOT_HEROPENEN
    """
    rule = SignalHandledRule()
    state = workflow.AFGEHANDELD

    def test_signal_set_state_second_time(self):
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertTrue(self.rule(signal))

        status = StatusFactory.create(_signal=signal, state=workflow.HEROPEND)
        signal.status = status
        signal.save()

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertTrue(self.rule(signal))

    def test_signal_set_state_second_time_second_last_state_verzoek_tot_heropenen(self):
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertTrue(self.rule(signal))

        status = StatusFactory.create(_signal=signal, state=workflow.VERZOEK_TOT_HEROPENEN)
        signal.status = status
        signal.save()

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertFalse(self.rule(signal))


class TestSignalScheduledRule(RuleTestMixin, TestCase):
    """
    Test the SignalScheduledRule. The rule should only be triggerd when the following rules apply:

    - The status is INGEPLAND
    - send_mail must be True
    """
    rule = SignalScheduledRule()
    send_email = True
    state = workflow.INGEPLAND


class TestSignalReopenedRule(RuleTestMixin, TestCase):
    """
    Test the SignalReopenedRule. The rule should only be triggerd when the following rules apply:

    - The status is HEROPEND
    """
    rule = SignalReopenedRule()
    state = workflow.HEROPEND


class TestSignalReactionRequestRule(RuleTestMixin, TestCase):
    """
    Test the SignalReactionRequestRule. The rule should only be triggerd when the following rules apply:

    - The status is REACTIE_GEVRAAGD
    """
    rule = SignalReactionRequestRule()
    state = workflow.REACTIE_GEVRAAGD


class TestSignalReactionRequestReceivedRule(RuleTestMixin, TestCase):
    """
    Test the SignalReactionRequestReceivedRule. The rule should only be triggerd when the following rules apply:

    - The status is REACTIE_ONTVANGEN
    - The status text does not match NO_REACTION_RECEIVED_TEXT
    """
    rule = SignalReactionRequestReceivedRule()
    state = workflow.REACTIE_ONTVANGEN

    def test_no_reaction_received(self):
        signal = SignalFactory.create(status__state=workflow.REACTIE_ONTVANGEN,
                                      status__text=NO_REACTION_RECEIVED_TEXT,
                                      reporter__email='test@example.com')

        self.assertFalse(self.rule(signal))


class TestSignalHandledNegative(RuleTestMixin, TestCase):

    rule = SignalHandledNegativeRule()
    state = workflow.AFGEHANDELD
    prev_state = workflow.VERZOEK_TOT_HEROPENEN

    def test_allows_contact_on_feedback(self):
        status_text = FuzzyText(length=400)

        # create signal in prev status
        signal = SignalFactory.create(status__state=self.prev_state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='test@example.com')

        # create the new current state
        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        feedback = FeedbackFactory.create(
            allows_contact=True,
            _signal=signal,
        )
        feedback.save()
        self.assertTrue(self.rule(signal))

    def test_happy_flow(self):
        status_text = FuzzyText(length=400)

        # create signal in prev status
        signal = SignalFactory.create(status__state=self.prev_state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='test@example.com')

        # create the new current state
        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        feedback = FeedbackFactory.create(
            allows_contact=True,
            _signal=signal,
        )
        feedback.save()
        self.assertTrue(self.rule(signal))

    def test_apply_for_parent_signals(self):
        status_text = FuzzyText(length=400)

        parent_signal = SignalFactory.create(status__state=self.prev_state, status__text=status_text,
                                             status__send_email=self.send_email, reporter__email='test@example.com')
        SignalFactory.create(status__state=self.state, status__text=status_text, reporter__email='test@example.com',
                             parent=parent_signal)

        # create the new current state
        status = StatusFactory.create(_signal=parent_signal, state=self.state)
        parent_signal.status = status
        parent_signal.save()

        feedback = FeedbackFactory.create(
            allows_contact=True,
            _signal=parent_signal,
        )
        feedback.save()

        self.assertTrue(self.rule(parent_signal))

    def test_no_feedback(self):
        status_text = FuzzyText(length=400)

        # create signal in prev status
        signal = SignalFactory.create(status__state=self.prev_state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='test@example.com')

        # create the new current state
        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertFalse(self.rule(signal))


class TestSignalOptionalRule(TestCase):
    """
    Test the SignalOptionalRule. The rule should only be triggerd when the following rules apply:

    - The status is GEMELD, AFWACHTING, BEHANDELING, ON_HOLD, VERZOEK_TOT_AFHANDELING or GEANNULEERD
    - send_mail must be True
    """
    rule = SignalOptionalRule()

    def test_statuses(self):
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        statuses = [
            workflow.GEMELD,
            workflow.AFWACHTING,
            workflow.BEHANDELING,
            workflow.ON_HOLD,
            workflow.VERZOEK_TOT_AFHANDELING,
            workflow.GEANNULEERD,
            workflow.INGEPLAND,
        ]

        for state in statuses:
            status = StatusFactory.create(_signal=signal, state=state, send_email=True)
            signal.status = status
            signal.save()

            self.assertTrue(self.rule(signal))

    def test_statuses_do_not_apply(self):
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        statuses = [
            workflow.GEMELD,
            workflow.AFWACHTING,
            workflow.BEHANDELING,
            workflow.ON_HOLD,
            workflow.VERZOEK_TOT_AFHANDELING,
            workflow.GEANNULEERD,
            workflow.INGEPLAND,
        ]

        for state in statuses:
            status = StatusFactory.create(_signal=signal, state=state, send_email=False)
            signal.status = status
            signal.save()

            self.assertFalse(self.rule(signal))

    def test_statuses_not_allowed(self):
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        statuses = [
            workflow.LEEG,
            workflow.AFGEHANDELD,
            workflow.GESPLITST,
            workflow.HEROPEND,
            workflow.VERZOEK_TOT_HEROPENEN,
            workflow.TE_VERZENDEN,
            workflow.VERZONDEN,
            workflow.VERZENDEN_MISLUKT,
            workflow.AFGEHANDELD_EXTERN,
            workflow.DOORGEZET_NAAR_EXTERN,
        ]

        for state in statuses:
            status = StatusFactory.create(_signal=signal, state=state, send_email=True)
            signal.status = status
            signal.save()

            self.assertFalse(self.rule(signal))


class TestForwardToExternalRule(TestCase):
    rule = ForwardToExternalRule()
    state = workflow.DOORGEZET_NAAR_EXTERN
    email_override = 'a@example.com'
    send_email = True

    def test_happy_flow(self):
        # we need email override to be set
        signal = SignalFactory.create(status__state=self.state, status__text='STATUS_TEXT',
                                      status__send_email=self.send_email,
                                      status__email_override='override@example.com',
                                      reporter__email='test@example.com')
        self.assertTrue(self.rule(signal))

    def test_email_override_none(self):
        # no email override set, mail should not be sent
        signal = SignalFactory.create(status__state=self.state, status__text='STATUS_TEXT',
                                      status__send_email=self.send_email, status__email_override=None,
                                      reporter__email='test@example.com')
        self.assertFalse(self.rule(signal))

    def test_email_override_invalid(self):
        # invalid email override set, mail should not be sent
        signal = SignalFactory.create(status__state=self.state, status__text='STATUS_TEXT',
                                      status__send_email=self.send_email,
                                      status__email_override='NOT_AN_EMAIL_ADDRESS',
                                      reporter__email='test@example.com')
        self.assertFalse(self.rule(signal))

    def test_anonymous_reporter(self):
        # we do not need reporter email
        signal = SignalFactory.create(status__state=self.state, status__text='STATUS_TEXT',
                                      status__email_override='override@example.com',
                                      reporter__email='')
        self.assertTrue(self.rule(signal))

    def test_apply_for_parent_signals(self):
        # we do not restrict the DOORGEZET_NAAR_EXTERN flow to parent or child signals, we check parent signals here
        parent_signal = SignalFactory.create(status__state=self.state,
                                             status__text='STATUS_TEXT',
                                             status__send_email=self.send_email,
                                             status__email_override='override@example.com',
                                             reporter__email='')
        SignalFactory.create(status__state=self.state,
                             status__text='STATUS_TEXT',
                             reporter__email='',
                             status__email_override='',
                             parent=parent_signal)
        self.assertTrue(self.rule(parent_signal))

    def test_apply_for_child_signals(self):
        # we do not restrict the DOORGEZET_NAAR_EXTERN flow to parent or child signals, we check child signals here
        parent_signal = SignalFactory.create(status__state=self.state,
                                             status__text='STATUS_TEXT',
                                             status__send_email=self.send_email,
                                             status__email_override='',
                                             reporter__email='')
        child_signal = SignalFactory.create(status__state=self.state,
                                            status__text='STATUS_TEXT',
                                            status__email_override='override@example.com',
                                            reporter__email='',
                                            parent=parent_signal)
        self.assertTrue(self.rule(child_signal))
