# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalCreatedRule

logger = logging.getLogger(__name__)


class SignalCreatedAction(AbstractAction):
    rule = SignalCreatedRule()

    key = EmailTemplate.SIGNAL_CREATED
    subject = 'Bedankt voor uw melding {signal_id}'

    note = 'Automatische e-mail bij registratie van de melding is verzonden aan de melder.'

    def get_additional_context(self, signal):
        return {
            'afhandelings_text': signal.category_assignment.category.handling_message
        }
