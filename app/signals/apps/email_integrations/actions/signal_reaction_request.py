# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
from signals.apps.email_integrations.actions.abstract import AbstractSignalStatusAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalReactionRequestRule
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.email_integrations.utils import create_reaction_request_and_mail_context
from signals.apps.signals.models import Signal


class SignalReactionRequestAction(AbstractSignalStatusAction):
    rule: AbstractRule = SignalReactionRequestRule()

    key: str = EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD
    subject: str = 'Meer over uw melding {formatted_signal_id}'

    note: str = 'E-mail met vraag verstuurd aan melder'

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        return create_reaction_request_and_mail_context(signal, dry_run)
