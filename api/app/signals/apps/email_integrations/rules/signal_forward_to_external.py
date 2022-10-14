# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals.workflow import DOORZETTEN_NAAR_EXTERN


class ForwardToExternalRule(AbstractRule):
    def _validate_status(self, status):
        """
        Run status validations for the Rule

        - The status is DOORZETTEN_NAAR_EXTERN
        """
        return self._validate_status_state(status)

    def _validate_status_state(self, status):
        """
        Validate that the status is DOORZETTEN_NAAR_EXTERN
        """
        return status.state == DOORZETTEN_NAAR_EXTERN
