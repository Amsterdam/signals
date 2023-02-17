# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalReactionRequestReceivedRule

logger = logging.getLogger(__name__)


class SignalReactionRequestReceivedAction(AbstractAction):
    rule = SignalReactionRequestReceivedRule()

    key = EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_ONTVANGEN
    subject = 'Meer over uw melding {formatted_signal_id}'

    note = 'Automatische e-mail bij Reactie ontvangen is verzonden aan de melder.'

    def get_additional_context(self, signal, dry_run=False):
        return {'reaction_request_answer': signal.status.text}
