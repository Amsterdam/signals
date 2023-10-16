# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
from signals.apps.email_integrations.actions.abstract import AbstractSignalStatusAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalHandledRule
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.email_integrations.utils import create_feedback_and_mail_context
from signals.apps.signals.models import Signal


class SignalHandledAction(AbstractSignalStatusAction):
    rule: AbstractRule = SignalHandledRule()

    key: str = EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD
    subject: str = 'Meer over uw melding {formatted_signal_id}'

    note: str = 'Automatische e-mail bij afhandelen is verzonden aan de melder.'

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        return create_feedback_and_mail_context(signal, dry_run)
