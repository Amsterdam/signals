# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import ForwardToExternalRule
from signals.apps.email_integrations.utils import create_external_reaction_request_and_mail_context

logger = logging.getLogger(__name__)


class SignalForwardToExternalAction(AbstractAction):
    rule = ForwardToExternalRule()

    key = EmailTemplate.SIGNAL_STATUS_CHANGED_OPTIONAL
    subject = 'Verzoek tot behandeling van Signalen melding {formatted_signal_id}'  # TODO: check phrasing PS-261

    note = 'Automatische e-mail bij doorzetten is verzonden aan externe partij.'

    def get_additional_context(self, signal, dry_run=False):
        return create_external_reaction_request_and_mail_context(signal, dry_run)
