# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals.workflow import REACTIE_GEVRAAGD


class SignalReactionRequestRule(AbstractRule):
    def _validate_status(self, status):
        """
        Run status validations for the Rule

        - The status is REACTIE_GEVRAAGD
        """
        return self._validate_status_state(status)

    def _validate_status_state(self, status):
        """
        Validate that the status is REACTIE_GEVRAAGD
        """
        return status.state == REACTIE_GEVRAAGD
