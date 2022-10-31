# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
import logging

from signals.apps.email_integrations.actions.abstract import AbstractSystemAction
from signals.apps.email_integrations.models import EmailTemplate

logger = logging.getLogger(__name__)


class ForwardToExternalReactionReceivedAction(AbstractSystemAction):
    _required_call_kwargs = ('reaction_text', 'email_override')
    rule = lambda self, signal: True  # noqa: E731

    key = EmailTemplate.SIGNAL_FORWARD_TO_EXTERNAL_REACTION_RECEIVED
    subject = 'Meldingen {formatted_signal_id}: reactie ontvangen'
    note = 'Automatische e-mail bij ontvangen van feedback is verzonden aan externe behandelaar'

    def get_email_address(self, signal):
        return self.kwargs['email_override']

    def get_additional_context(self, signal, dry_run=False):
        return {'reaction_text': self.kwargs['reaction_text']}
