# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
from signals.apps.email_integrations.actions.abstract import AbstractSignalStatusAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalOptionalRule
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.signals.models import Signal


class SignalOptionalAction(AbstractSignalStatusAction):
    rule: AbstractRule = SignalOptionalRule()

    key: str = EmailTemplate.SIGNAL_STATUS_CHANGED_OPTIONAL
    subject: str = 'Meer over uw melding {formatted_signal_id}'

    note: str = 'De statusupdate is per e-mail verzonden aan de melder'

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        assert signal.status is not None

        return {
            'afhandelings_text': signal.status.text
        }
