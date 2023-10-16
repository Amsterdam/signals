# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
from signals.apps.email_integrations.actions.abstract import AbstractSignalStatusAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalReactionRequestReceivedRule
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals.models import Signal


class SignalReactionRequestReceivedAction(AbstractSignalStatusAction):
    rule: AbstractRule = SignalReactionRequestReceivedRule()

    key: str = EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_ONTVANGEN
    subject: str = 'Meer over uw melding {formatted_signal_id}'

    note: str = 'Automatische e-mail bij Reactie ontvangen is verzonden aan de melder.'

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        return {'reaction_request_answer': signal.status.text}
