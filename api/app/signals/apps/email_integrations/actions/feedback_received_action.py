# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging

from django.conf import settings

from signals.apps.email_integrations.actions.abstract import AbstractSystemAction
from signals.apps.email_integrations.models import EmailTemplate

logger = logging.getLogger(__name__)


class FeedbackReceivedAction(AbstractSystemAction):
    _required_call_kwargs = ('feedback',)

    # Rule must check if the feature flag for this system mail is enabled
    rule = lambda self, signal: settings.FEATURE_FLAGS.get('SYSTEM_MAIL_FEEDBACK_RECEIVED_ENABLED', True)  # noqa: E731

    key = EmailTemplate.SIGNAL_FEEDBACK_RECEIVED
    subject = 'Bedankt voor uw feedback'
    note = 'Automatische e-mail bij ontvangen van feedback is verzonden aan de melder.'

    def get_additional_context(self, signal, dry_run=False):
        return {
            'feedback_allows_contact': self.kwargs['feedback'].allows_contact,
            'feedback_is_satisfied': self.kwargs['feedback'].is_satisfied,
            'feedback_text': self.kwargs['feedback'].text,
            'feedback_text_extra': self.kwargs['feedback'].text_extra
        }
