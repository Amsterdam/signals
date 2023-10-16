# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
from django.conf import settings

from signals.apps.email_integrations.actions.abstract import AbstractSystemAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.signals.models import Signal


class FeedbackReceivedAction(AbstractSystemAction):
    _required_call_kwargs: list[str] = ['feedback']

    key: str = EmailTemplate.SIGNAL_FEEDBACK_RECEIVED
    subject: str = 'Bedankt voor uw feedback'
    note: str = 'Automatische e-mail bij ontvangen van feedback is verzonden aan de melder.'

    def _validate(self) -> bool:
        return settings.FEATURE_FLAGS.get('SYSTEM_MAIL_FEEDBACK_RECEIVED_ENABLED', True)

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        assert self.kwargs is not None

        return {
            'feedback_allows_contact': self.kwargs['feedback'].allows_contact,
            'feedback_is_satisfied': self.kwargs['feedback'].is_satisfied,
            'feedback_text': self.kwargs['feedback'].text,
            'feedback_text_extra': self.kwargs['feedback'].text_extra,
            'feedback_text_list': self.kwargs['feedback'].text_list
        }
