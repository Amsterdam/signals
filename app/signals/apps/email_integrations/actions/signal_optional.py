# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalOptionalRule

logger = logging.getLogger(__name__)


class SignalOptionalAction(AbstractAction):
    rule = SignalOptionalRule()

    key = EmailTemplate.SIGNAL_STATUS_CHANGED_OPTIONAL
    subject = 'Meer over uw melding {formatted_signal_id}'

    note = 'De statusupdate is per e-mail verzonden aan de melder'

    def get_additional_context(self, signal, dry_run=False):
        return {
            'afhandelings_text': signal.status.text
        }
