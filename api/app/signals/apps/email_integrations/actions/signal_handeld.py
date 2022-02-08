# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalHandledRule
from signals.apps.email_integrations.utils import create_feedback_and_mail_context

logger = logging.getLogger(__name__)


class SignalHandledAction(AbstractAction):
    rule = SignalHandledRule()

    key = EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD
    subject = 'Meer over uw melding {signal_id}'

    note = 'Automatische e-mail bij afhandelen is verzonden aan de melder.'

    def get_additional_context(self, signal):
        return create_feedback_and_mail_context(signal)
