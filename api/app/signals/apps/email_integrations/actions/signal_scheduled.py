# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import logging

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalScheduledRule

logger = logging.getLogger(__name__)


class SignalScheduledAction(AbstractAction):
    rule = SignalScheduledRule()

    key = EmailTemplate.SIGNAL_STATUS_CHANGED_INGEPLAND
    subject = 'Meer over uw melding {signal_id}'

    note = 'Automatische e-mail bij inplannen is verzonden aan de melder.'
