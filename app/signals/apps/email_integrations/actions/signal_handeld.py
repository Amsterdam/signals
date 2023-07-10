# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
import typing

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalHandledRule
from signals.apps.email_integrations.utils import create_feedback_and_mail_context
from signals.apps.signals.models import Signal


class SignalHandledAction(AbstractAction):
    rule: typing.Callable[[Signal], bool] = SignalHandledRule()

    key: str = EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD
    subject: str = 'Meer over uw melding {formatted_signal_id}'

    note: str = 'Automatische e-mail bij afhandelen is verzonden aan de melder.'

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        return create_feedback_and_mail_context(signal, dry_run)
