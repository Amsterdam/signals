# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals import workflow


class SignalHandledRule(AbstractRule):
    def _validate(self, signal):
        """
        Run all validations for the Rule

        - The status is AFGEHANDELD
        - The previous state is not VERZOEK_TOT_HEROPENEN
        """
        return (self._validate_status(signal.status.state) and
                self._validate_previous_state_not_VERZOEK_TOT_HEROPENEN(signal))

    def _validate_status(self, state):
        """
        Validate if the status is AFGEHANDELD
        """
        return state == workflow.AFGEHANDELD

    def _validate_previous_state_not_VERZOEK_TOT_HEROPENEN(self, signal):
        """
        Validate if the previous state is not VERZOEK_TOT_HEROPENEN
        """
        return signal.statuses.exclude(
            id=signal.status_id
        ).order_by(
            '-created_at'
        ).values_list(
            'state',
            flat=True
        ).first() != workflow.VERZOEK_TOT_HEROPENEN
