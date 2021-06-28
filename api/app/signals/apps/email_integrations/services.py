# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from signals.apps.email_integrations.actions import (
    SignalCreatedAction,
    SignalHandledAction,
    SignalOptionalAction,
    SignalReopenedAction,
    SignalScheduledAction
)
from signals.apps.signals.models import Signal


class MailService:
    actions = (
        SignalCreatedAction(),
        SignalHandledAction(),
        SignalScheduledAction(),
        SignalReopenedAction(),
        SignalOptionalAction(),
    )

    @staticmethod
    def mail(signal):
        if not isinstance(signal, Signal):
            signal = Signal.objects.get(pk=signal)

        for action in MailService.actions:
            if action(signal):
                return True

        return False
