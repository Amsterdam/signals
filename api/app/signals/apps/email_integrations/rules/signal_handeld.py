# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals import workflow


class SignalHandledRule(AbstractRule):
    def validate_status(self, signal):
        """
        Validate if the status is AFGEHANDELD and previous state must not be VERZOEK_TOT_HEROPENEN
        """
        return signal.status.state == workflow.AFGEHANDELD and signal.statuses.exclude(
            id=signal.status_id
        ).order_by(
            '-created_at'
        ).values_list(
            'state',
            flat=True
        ).first() != workflow.VERZOEK_TOT_HEROPENEN
