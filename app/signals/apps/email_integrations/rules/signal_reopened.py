# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals.workflow import HEROPEND


class SignalReopenedRule(AbstractRule):
    def _validate_status(self, status):
        """
        Run status validations for the Rule

        - The status is HEROPEND
        """
        return self._validate_status_state(status)

    def _validate_status_state(self, status):
        """
        Validate that the status is HEROPEND
        """
        return status.state == HEROPEND
