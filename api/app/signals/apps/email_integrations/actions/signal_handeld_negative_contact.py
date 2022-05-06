# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import logging

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalHandledNegativeRule

logger = logging.getLogger(__name__)


class SignalHandledNegativeAction(AbstractAction):
    rule = SignalHandledNegativeRule()

    key = EmailTemplate.Signal_STATUS_CHANGED_AFGEHANDELD_KTO_NEGATIVE_CONTACT
    subject = 'Meer over uw melding {signal_id}'

    note = 'Automatische e-mail bij afhandelen heropenen negatieve feedback'
