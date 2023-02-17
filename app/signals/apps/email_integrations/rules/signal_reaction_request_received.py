# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.questionnaires.app_settings import NO_REACTION_RECEIVED_TEXT
from signals.apps.signals.workflow import REACTIE_ONTVANGEN


class SignalReactionRequestReceivedRule(AbstractRule):
    def _validate_status(self, status):
        """
        Run status validations for the Rule

        - The status is REACTIE_ONTVANGEN
        - The status text does not match NO_REACTION_RECEIVED_TEXT
        """
        return self._validate_status_state(status) and self._validate_status_text(status)

    def _validate_status_state(self, status):
        """
        Validate that the status is REACTIE_ONTVANGEN
        """
        return status.state == REACTIE_ONTVANGEN

    def _validate_status_text(self, status):
        """
        Validate that the status text does not match NO_REACTION_RECEIVED_TEXT
        """
        return status.text.lower() != NO_REACTION_RECEIVED_TEXT.lower()
