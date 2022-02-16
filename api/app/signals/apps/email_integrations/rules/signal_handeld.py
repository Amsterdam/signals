# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals.workflow import AFGEHANDELD, VERZOEK_TOT_HEROPENEN


class SignalHandledRule(AbstractRule):
    def _validate(self, signal):
        return self._validate_previous_state_not_VERZOEK_TOT_HEROPENEN(signal)

    def _validate_status(self, status):
        """
        Run status validations for the Rule

        - The status is AFGEHANDELD
        - The previous state is not VERZOEK_TOT_HEROPENEN
        """
        return self._validate_status_state(status)

    def _validate_status_state(self, status):
        """
        Validate that the status is AFGEHANDELD
        """
        return status.state == AFGEHANDELD

    def _validate_previous_state_not_VERZOEK_TOT_HEROPENEN(self, signal):
        """
        Validate that the previous state is not VERZOEK_TOT_HEROPENEN
        """
        return signal.statuses.exclude(
            id=signal.status_id
        ).order_by(
            '-created_at'
        ).values_list(
            'state',
            flat=True
        ).first() != VERZOEK_TOT_HEROPENEN
