# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalReopenedRule

logger = logging.getLogger(__name__)


class SignalReopenedAction(AbstractAction):
    rule = SignalReopenedRule()

    key = EmailTemplate.SIGNAL_STATUS_CHANGED_HEROPEND
    subject = 'Meer over uw melding {signal_id}'

    note = 'Automatische e-mail bij heropenen is verzonden aan de melder.'
