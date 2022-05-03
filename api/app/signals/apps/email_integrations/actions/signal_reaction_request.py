# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalReactionRequestRule
from signals.apps.email_integrations.utils import create_reaction_request_and_mail_context

logger = logging.getLogger(__name__)


class SignalReactionRequestAction(AbstractAction):
    rule = SignalReactionRequestRule()

    key = EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD
    subject = 'Meer over uw melding {signal_id}'

    note = 'E-mail met vraag verstuurd aan melder'

    def get_additional_context(self, signal, dry_run=False, **kwargs):
        return create_reaction_request_and_mail_context(signal, dry_run)
