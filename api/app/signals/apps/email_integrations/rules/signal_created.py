# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals import workflow


class SignalCreatedRule(AbstractRule):
    def _validate(self, signal):
        """
        Run all validations for the Rule

        - The status is GEMELD
        - The status GEMELD is set only once
        """
        return self._validate_status(signal.status.state) and self._validate_status_GEMELD_set_once(signal)

    def _validate_status(self, state):
        """
        Validate that the status is GEMELD
        """
        return state == workflow.GEMELD

    def _validate_status_GEMELD_set_once(self, signal):
        """
        Validate that the status GEMELD is set only once
        """
        return signal.statuses.filter(state=workflow.GEMELD).count() == 1
