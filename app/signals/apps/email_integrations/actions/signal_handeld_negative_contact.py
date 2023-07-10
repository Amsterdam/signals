# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import typing

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalHandledNegativeRule
from signals.apps.signals.models import Signal


class SignalHandledNegativeAction(AbstractAction):
    rule: typing.Callable[[Signal], bool] = SignalHandledNegativeRule()

    key: str = EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD_KTO_NEGATIVE_CONTACT
    subject: str = 'Meer over uw melding {formatted_signal_id}'

    note: str = 'Automatische e-mail bij afhandelen heropenen negatieve feedback'

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        """
        Add the extra feedback essences to the email template
        """
        feedback = signal.feedback.last()

        if not feedback:
            return {}

        return {
            'feedback_allows_contact': feedback.allows_contact,
            'feedback_is_satisfied': feedback.is_satisfied,
            'feedback_text': feedback.text,
            'feedback_text_extra': feedback.text_extra,
            'feedback_text_list': feedback.text_list,
        }
