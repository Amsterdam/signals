# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals import workflow


class SignalCreatedRule(AbstractRule):
    def validate_status(self, signal):
        """
        Validate if the status is GEMELD and that it is the first GEMELD status
        """
        return signal.status.state == workflow.GEMELD and signal.statuses.filter(state=workflow.GEMELD).count() == 1
