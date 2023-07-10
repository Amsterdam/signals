# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
import typing

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import ForwardToExternalRule
from signals.apps.email_integrations.utils import create_forward_to_external_and_mail_context
from signals.apps.signals.models import Signal


class SignalForwardToExternalAction(AbstractAction):
    rule: typing.Callable[[Signal], bool] = ForwardToExternalRule()
    key: str = EmailTemplate.SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL
    subject: str = 'Verzoek tot behandeling van Signalen melding {formatted_signal_id}'

    fallback_txt_template: str = 'email/signal_forward_to_external.txt'
    fallback_html_template: str = 'email/signal_forward_to_external.html'

    note: str = 'Automatische e-mail bij doorzetten is verzonden aan externe partij.'

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        return create_forward_to_external_and_mail_context(signal, dry_run)

    def get_recipient_list(self, signal: Signal) -> list[str]:
        return [signal.status.email_override]
