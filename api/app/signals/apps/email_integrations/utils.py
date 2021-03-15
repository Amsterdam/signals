# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import re
from typing import Optional

from django.conf import settings

from signals.apps.feedback.models import Feedback
from signals.apps.feedback.utils import get_feedback_urls
from signals.apps.signals.models import Signal


def _create_feedback_and_mail_context(signal: Signal):
    """
    Util functions to create the feedback object and create the context needed for the mail
    """
    feedback = Feedback.actions.request_feedback(signal)
    positive_feedback_url, negative_feedback_url = get_feedback_urls(feedback)
    return {
        'negative_feedback_url': negative_feedback_url,
        'positive_feedback_url': positive_feedback_url,
    }


def make_email_context(signal: Signal, additional_context: Optional[dict] = None) -> dict:
    """
    Makes a context dictionary containing all values needed for the email templates
    Can add additional context, but will make sure that none of the default values are overridden.

    For backwards compatibility the Signal and the Status are still added to the context
    """

    # Pattern used to filter links from the Signal text and text_extra
    url_pattern = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

    context = {
        'signal_id': signal.id,
        'formatted_signal_id': signal.sia_id,
        'created_at': signal.created_at,
        'text': re.sub(url_pattern, '', signal.text),
        'text_extra': re.sub(url_pattern, '', signal.text_extra),
        'address': signal.location.address,
        'status_text': signal.status.text,
        'status_state': signal.status.state,
        'handling_message': signal.category_assignment.stored_handling_message,
        'ORGANIZATION_NAME': settings.ORGANIZATION_NAME,

        # Backwards compatibility items
        # TODO: Remove these items when all templates are updated to use the new context variables
        'signal': signal,
        'status': signal.status,
        'location': signal.location,
    }

    if additional_context:
        # Make sure the additional_context do not override the default context values
        for key in set(context).intersection(set(additional_context)):
            additional_context.pop(key)
        # Add the additional context
        context.update(additional_context)

    return context
