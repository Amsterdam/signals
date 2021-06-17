# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import re
from typing import Optional

from django.conf import settings
from django.core.validators import URLValidator
from django.template import Context, Template
from django.utils.timezone import now

from signals.apps.email_integrations.admin import EmailTemplate
from signals.apps.feedback.models import Feedback
from signals.apps.feedback.utils import get_feedback_urls
from signals.apps.questionnaires.services import ReactionRequestService
from signals.apps.signals.models import Signal
from tests.apps.signals.valid_locations import STADHUIS


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


def create_reaction_request_and_mail_context(signal: Signal):
    """
    Util function to create a question, questionnaire and prepared session for reaction request mails
    """
    session = ReactionRequestService.create_session(signal)
    reaction_url = ReactionRequestService.get_reaction_url(session)

    return {'reaction_url': reaction_url}


# Pattern used to filter links from the Signal text and text_extra
# Let's use the regex that is also used by Django to validate a URL (URLValidator)
# We only removed the ^ and the \Z because we want to search in a text for URL's
URL_PATTERN = re.compile(
    r'(?:[a-z0-9\.\-\+]*://)?'
    r'(?:[^\s:@/]+(?::[^\s:@/]*)?@)?'
    r'(?:' + URLValidator.ipv4_re + '|' + URLValidator.ipv6_re + '|' + URLValidator.host_re + ')'
    r'(?::\d{2,5})?'
    r'(?:[/?#][^\s]*)?', re.IGNORECASE
)


def make_email_context(signal: Signal, additional_context: Optional[dict] = None) -> dict:
    """
    Makes a context dictionary containing all values needed for the email templates
    Can add additional context, but will make sure that none of the default values are overridden.

    For backwards compatibility the Signal and the Status are still added to the context
    """
    context = {
        'signal_id': signal.id,
        'formatted_signal_id': signal.sia_id,
        'created_at': signal.created_at,
        'text': re.sub(URL_PATTERN, '', signal.text),
        'text_extra': re.sub(URL_PATTERN, '', signal.text_extra),
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


def validate_email_template(email_template: EmailTemplate) -> bool:
    """
    Used to validate an EmailTemplate
    """
    return validate_template(template=email_template.title) and validate_template(template=email_template.body)


def validate_template(template: str) -> bool:
    """
    Used to validate an template string with a dummy context
    """
    context = {
        'signal_id': 123,
        'formatted_signal_id': 'SIA-123',
        'created_at': now(),
        'text': 'Deze tekst wordt gebruikt in de validatie van een EmailTemplate.',
        'text_extra': 'Er is ruimte voor meer tekst.',
        'address': STADHUIS,
        'status_text': 'Gemeld',
        'status_state': 'm',
        'handling_message': 'Hartelijk dank voor uw melding. Wij gaan hier spoedig mee aan de slag',
        'ORGANIZATION_NAME': settings.ORGANIZATION_NAME
    }

    try:
        body_template = Template(template)
        body_template.render(context=Context(context, autoescape=True))
    except Exception:
        return False
    else:
        return True
