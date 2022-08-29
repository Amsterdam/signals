# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from typing import Union

from signals.apps.email_integrations.actions import (
    FeedbackReceivedAction,
    AssignedAction,
    SignalCreatedAction,
    SignalHandledAction,
    SignalHandledNegativeAction,
    SignalOptionalAction,
    SignalReactionRequestAction,
    SignalReactionRequestReceivedAction,
    SignalReopenedAction,
    SignalScheduledAction
)
from signals.apps.signals.models import Signal


class MailService:

    # Status actions are used when signals change status and are verified with
    # the rule parameters inside the actions
    _status_actions = (
        SignalCreatedAction(),
        SignalHandledAction(),
        SignalScheduledAction(),
        SignalReopenedAction(),
        SignalOptionalAction(),
        SignalReactionRequestAction(),
        SignalReactionRequestReceivedAction(),
        SignalHandledNegativeAction()
    )
    # System actions are use to send specific emails
    # they do not have a rule and wil always trigger and should NOT be added to the status_actions
    _system_actions = {
        'feedback_received': FeedbackReceivedAction,
        'assigned': AssignedAction,
    }

    @classmethod
    def status_mail(cls, signal, dry_run=False) -> bool:
        """
        Send a mail based on the update status from a signal
        """
        if not isinstance(signal, Signal):
            signal = Signal.objects.get(pk=signal)

        for action in cls._status_actions:
            if action(signal, dry_run=dry_run):
                return True

        return False

    @classmethod
    def system_mail(cls, signal: Union[str, Signal], action_name: str, dry_run=False, recipient_list=[], **kwargs) -> bool:
        """
        Send a specific mail trigger based on the trigger name
        """
        action = cls._system_actions.get(action_name)()
        if not action:
            raise NotImplementedError(f'{action_name} is not implemented')

        if not isinstance(signal, Signal):
            signal = Signal.objects.get(pk=signal)

        if dry_run:
            return True

        return action(signal, dry_run, recipient_list, **kwargs)
