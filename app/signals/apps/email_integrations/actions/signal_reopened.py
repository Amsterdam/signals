# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
from signals.apps.email_integrations.actions.abstract import AbstractSignalStatusAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalReopenedRule
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals.models import Signal


class SignalReopenedAction(AbstractSignalStatusAction):
    rule: AbstractRule = SignalReopenedRule()

    key: str = EmailTemplate.SIGNAL_STATUS_CHANGED_HEROPEND
    subject: str = 'Meer over uw melding {formatted_signal_id}'

    note: str = 'Automatische e-mail bij heropenen is verzonden aan de melder.'

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        feedback_qs = signal.feedback.filter(submitted_at__isnull=False)
        feedback_received = feedback_qs.exists()

        if feedback_received:
            last_received_feedback = feedback_qs.order_by('submitted_at').last()
            assert last_received_feedback is not None

            feedback_is_satisfied = last_received_feedback.is_satisfied
            feedback_text = last_received_feedback.text
            feedback_text_extra = last_received_feedback.text_extra
            feedback_text_list = last_received_feedback.text_list
        else:
            feedback_is_satisfied = None
            feedback_text = None
            feedback_text_extra = None
            feedback_text_list = None

        return {
            'feedback_received': feedback_received,
            'feedback_is_satisfied': feedback_is_satisfied,
            'feedback_text': feedback_text,
            'feedback_text_extra': feedback_text_extra,
            'feedback_text_list': feedback_text_list,
        }
