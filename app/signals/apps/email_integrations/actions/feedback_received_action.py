# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
import typing

from django.conf import settings

from signals.apps.email_integrations.actions.abstract import AbstractSystemAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.signals.models import Signal


class FeedbackReceivedAction(AbstractSystemAction):
    _required_call_kwargs: list[str] = ('feedback',)

    # Rule must check if the feature flag for this system mail is enabled
    rule: typing.Callable[[Signal], bool] = \
        lambda self, signal: settings.FEATURE_FLAGS.get('SYSTEM_MAIL_FEEDBACK_RECEIVED_ENABLED', True)

    key: str = EmailTemplate.SIGNAL_FEEDBACK_RECEIVED
    subject: str = 'Bedankt voor uw feedback'
    note: str = 'Automatische e-mail bij ontvangen van feedback is verzonden aan de melder.'

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        return {
            'feedback_allows_contact': self.kwargs['feedback'].allows_contact,
            'feedback_is_satisfied': self.kwargs['feedback'].is_satisfied,
            'feedback_text': self.kwargs['feedback'].text,
            'feedback_text_extra': self.kwargs['feedback'].text_extra,
            'feedback_text_list': self.kwargs['feedback'].text_list
        }
