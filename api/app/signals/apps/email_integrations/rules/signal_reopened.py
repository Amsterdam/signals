# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals import workflow


class SignalReopenedRule(AbstractRule):
    def validate_status(self, signal):
        """
        Validate if the status is HEROPEND
        """
        return signal.status.state == workflow.HEROPEND
