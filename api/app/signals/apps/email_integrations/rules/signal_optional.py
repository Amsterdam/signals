# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals import workflow


class SignalOptionalRule(AbstractRule):
    def _validate_status(self, status):
        """
        Run status validations for the Rule

        - The status is GEMELD, AFWACHTING, BEHANDELING, ON_HOLD, VERZOEK_TOT_AFHANDELING or GEANNULEERD
        - send_mail must be True
        """
        return self._validate_status_state(status) and self._validate_status_send_mail(status)

    def _validate_status_state(self, status):
        """
        Validate that the status is GEMELD, AFWACHTING, BEHANDELING, ON_HOLD, VERZOEK_TOT_AFHANDELING or GEANNULEERD
        """
        return status.state in [
            workflow.GEMELD,
            workflow.AFWACHTING,
            workflow.BEHANDELING,
            workflow.ON_HOLD,
            workflow.VERZOEK_TOT_AFHANDELING,
            workflow.GEANNULEERD,
        ]

    def _validate_status_send_mail(self, status):
        return status.send_email
