# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals import workflow


class SignalOptionalRule(AbstractRule):
    def validate_status(self, signal):
        """
        Validate if the status is GEMELD, AFWACHTING, BEHANDELING, ON_HOLD, VERZOEK_TOT_AFHANDELING or GEANNULEERD
        """
        return signal.status.state in [
            workflow.GEMELD,
            workflow.AFWACHTING,
            workflow.BEHANDELING,
            workflow.ON_HOLD,
            workflow.VERZOEK_TOT_AFHANDELING,
            workflow.GEANNULEERD,
        ] and signal.status.send_email
