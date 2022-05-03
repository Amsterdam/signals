# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging

from signals.apps.email_integrations.actions.abstract import AbstractAction
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.feedback.models import Feedback

logger = logging.getLogger(__name__)


class FeedbackReceivedAction(AbstractAction):

    rule = None  # There is no rule as this action is only being used for the system emails

    key = EmailTemplate.SIGNAL_FEEDBACK_RECEIVED
    subject = 'Bedankt voor uw feedback'
    note = 'Automatische e-mail bij ontvangen van feedback is verzonden aan de melder.'

    def get_additional_context(self, signal, dry_run=False, **kwargs):
        try:
            feedback = Feedback.objects.get(token=kwargs.get("feedback_token"))
        except Feedback.DoesNotExist:
            return {
                'feedback_text': '',
                'feedback_text_extra': ''
            }

        return {
            'feedback_text': feedback.text,
            'feedback_text_extra': feedback.text_extra
        }
