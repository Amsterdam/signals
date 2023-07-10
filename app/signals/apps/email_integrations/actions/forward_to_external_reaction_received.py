# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from signals.apps.email_integrations.actions.abstract import AbstractSystemAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.signals.models import Signal


class ForwardToExternalReactionReceivedAction(AbstractSystemAction):
    _required_call_kwargs: list[str] = ('reaction_text', 'email_override')

    key: str = EmailTemplate.SIGNAL_FORWARD_TO_EXTERNAL_REACTION_RECEIVED
    subject: str = 'Melding {formatted_signal_id}: reactie ontvangen'

    fallback_txt_template: str = 'email/forward_to_external_reaction_received.txt'
    fallback_html_template: str = 'email/forward_to_external_reaction_received.html'

    def get_recipient_list(self, signal: Signal) -> list[str]:
        return [self.kwargs['email_override']]

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        return {'reaction_text': self.kwargs['reaction_text']}
