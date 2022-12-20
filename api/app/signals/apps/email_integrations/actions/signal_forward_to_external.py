# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import logging

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import ForwardToExternalRule
from signals.apps.email_integrations.utils import create_forward_to_external_and_mail_context

logger = logging.getLogger(__name__)


class SignalForwardToExternalAction(AbstractAction):
    rule = ForwardToExternalRule()
    key = EmailTemplate.SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL
    subject = 'Verzoek tot behandeling van Signalen melding {formatted_signal_id}'  # TODO: check phrasing PS-261

    fallback_txt_template = 'email/signal_forward_to_external.txt'
    fallback_html_template = 'email/signal_forward_to_external.html'

    note = 'Automatische e-mail bij doorzetten is verzonden aan externe partij.'

    def get_additional_context(self, signal, dry_run=False):
        return create_forward_to_external_and_mail_context(signal, dry_run)

    def get_recipient_list(self, signal):
        return [signal.status.email_override]
