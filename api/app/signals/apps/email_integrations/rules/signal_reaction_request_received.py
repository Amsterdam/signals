# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.questionnaires.app_settings import NO_REACTION_RECEIVED_TEXT
from signals.apps.signals import workflow


class SignalReactionRequestReceivedRule(AbstractRule):
    def validate_status(self, signal):
        """
        Validate if the status is REACTIE_ONTVANGEN and status text does not match NO_REACTION_RECEIVED_TEXT
        """
        return (signal.status.state == workflow.REACTIE_ONTVANGEN and
                signal.status.text.lower() != NO_REACTION_RECEIVED_TEXT.lower())
