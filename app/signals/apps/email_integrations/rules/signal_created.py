# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals.models import Status
from signals.apps.signals.workflow import GEMELD


class SignalCreatedRule(AbstractRule):
    def _validate_status(self, status):
        """
        Run status validations for the Rule

        - The status is GEMELD
        - The status GEMELD is the first and currently set status
        """
        return self._validate_status_state(status) and self._validate_status_GEMELD_set_once(status)

    def _validate_status_state(self, status):
        """
        Validate that the status is GEMELD
        """
        return status.state == GEMELD

    def _validate_status_GEMELD_set_once(self, status):
        """
        Validate that this is the first status GEMELD for the signal
        """
        first_status = Status.objects.filter(_signal_id=status._signal_id).order_by('created_at').first()
        return status.id == first_status.id and first_status.state == GEMELD
