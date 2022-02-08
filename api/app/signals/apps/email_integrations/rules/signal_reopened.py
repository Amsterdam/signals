# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals import workflow


class SignalReopenedRule(AbstractRule):
    def validate(self, signal):
        """
        Run all validations for the Rule

        - The status is HEROPEND
        """
        return self._validate_status(signal.status.state)

    def _validate_status(self, state):
        """
        Validate if the status is HEROPEND
        """
        return state == workflow.HEROPEND
