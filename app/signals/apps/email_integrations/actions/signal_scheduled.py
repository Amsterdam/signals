# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
import typing

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import SignalScheduledRule
from signals.apps.signals.models import Signal


class SignalScheduledAction(AbstractAction):
    rule: typing.Callable[[Signal], bool] = SignalScheduledRule()

    key: str = EmailTemplate.SIGNAL_STATUS_CHANGED_INGEPLAND
    subject: str = 'Meer over uw melding {formatted_signal_id}'

    note: str = 'Automatische e-mail bij inplannen is verzonden aan de melder.'
