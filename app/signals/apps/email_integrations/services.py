# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from signals.apps.email_integrations.actions import (
    AssignedAction,
    FeedbackReceivedAction,
    ForwardToExternalReactionReceivedAction,
    SignalCreatedAction,
    SignalForwardToExternalAction,
    SignalHandledAction,
    SignalHandledNegativeAction,
    SignalOptionalAction,
    SignalReactionRequestAction,
    SignalReactionRequestReceivedAction,
    SignalReopenedAction,
    SignalScheduledAction
)
from signals.apps.email_integrations.actions.abstract import AbstractAction, AbstractSystemAction
from signals.apps.email_integrations.renderers.email_template_renderer import EmailTemplateRenderer
from signals.apps.signals.models import Signal


class MailService:

    # Status actions are used when signals change status and are verified with
    # the rule parameters inside the actions
    _status_actions: list[AbstractAction] = [
        SignalCreatedAction(EmailTemplateRenderer()),
        SignalHandledAction(EmailTemplateRenderer()),
        SignalScheduledAction(EmailTemplateRenderer()),
        SignalReopenedAction(EmailTemplateRenderer()),
        SignalOptionalAction(EmailTemplateRenderer()),
        SignalReactionRequestAction(EmailTemplateRenderer()),
        SignalReactionRequestReceivedAction(EmailTemplateRenderer()),
        SignalHandledNegativeAction(EmailTemplateRenderer()),
        SignalForwardToExternalAction(EmailTemplateRenderer()),  # PS-261
    ]
    # System actions are used to send specific emails
    # they do not have a rule and wil always trigger and should NOT be added to the status_actions
    _system_actions: dict[str, type[AbstractSystemAction]] = {
        'feedback_received': FeedbackReceivedAction,
        'forward_to_external_reaction_received': ForwardToExternalReactionReceivedAction,
        'assigned': AssignedAction,
    }

    @classmethod
    def status_mail(cls, signal: int | Signal, dry_run: bool = False) -> bool:
        """
        Send a mail based on the update status from a signal
        """
        if not isinstance(signal, Signal):
            signal = Signal.objects.select_related('status').get(pk=signal)

        assert isinstance(signal, Signal)

        for action in cls._status_actions:
            if action(signal, dry_run=dry_run):
                return True

        return False

    @classmethod
    def system_mail(cls, signal: int | Signal, action_name: str, dry_run: bool = False, **kwargs) -> bool:
        """
        Send a specific mail trigger based on the trigger name
        """
        action_type = cls._system_actions.get(action_name)
        assert action_type is not None
        action = action_type(EmailTemplateRenderer())
        if not action:
            raise NotImplementedError(f'{action_name} is not implemented')

        if not isinstance(signal, Signal):
            signal = Signal.objects.get(pk=signal)

        if dry_run:
            return True

        return action(signal, dry_run, **kwargs)
