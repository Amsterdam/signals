# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.questionnaires.app_settings import NO_REACTION_RECEIVED_TEXT
from signals.apps.signals import workflow


class SignalReactionRequestReceivedRule(AbstractRule):
    def _validate(self, signal):
        """
        Run all validations for the Rule

        - The status is REACTIE_ONTVANGEN
        - The status text does not match NO_REACTION_RECEIVED_TEXT
        """
        return self._validate_status(signal.status.state) and self._validate_status_text(signal.status.text)

    def _validate_status(self, state):
        """
        Validate if the status is REACTIE_ONTVANGEN
        """
        return state == workflow.REACTIE_ONTVANGEN

    def _validate_status_text(self, text):
        """
        Validate if the status text does not match NO_REACTION_RECEIVED_TEXT
        """
        return text.lower() != NO_REACTION_RECEIVED_TEXT.lower()
