# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
import typing

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalReactionRequestRule
from signals.apps.email_integrations.utils import create_reaction_request_and_mail_context
from signals.apps.signals.models import Signal


class SignalReactionRequestAction(AbstractAction):
    rule: typing.Callable[[Signal], bool] = SignalReactionRequestRule()

    key: str = EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD
    subject: str = 'Meer over uw melding {formatted_signal_id}'

    note: str = 'E-mail met vraag verstuurd aan melder'

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        return create_reaction_request_and_mail_context(signal, dry_run)
