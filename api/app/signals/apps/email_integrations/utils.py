# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import re
from typing import Optional
from urllib.parse import unquote

from django.conf import settings
from django.core.validators import URLValidator
from django.template import Context, Template
from django.utils.timezone import now
from mistune import create_markdown

from signals.apps.email_integrations.admin import EmailTemplate
from signals.apps.email_integrations.exceptions import URLEncodedCharsFoundInText
from signals.apps.feedback.models import Feedback
from signals.apps.feedback.utils import get_feedback_urls as get_feedback_urls_no_questionnaires
from signals.apps.questionnaires.services.feedback_request import (
    create_session_for_feedback_request,
    get_feedback_urls
)
from signals.apps.questionnaires.services.reaction_request import (
    create_session_for_reaction_request,
    get_reaction_url
)
from signals.apps.signals.models import Signal, Status
from signals.apps.signals.tests.valid_locations import STADHUIS


def create_feedback_and_mail_context(signal: Signal, dry_run=False) -> dict:
    """
    Util functions to create the feedback object and create the context needed for the mail
    """
    # Note: While the questionnaires app support for feedback requests is under
    # development we support both the "new" flow and the "old". Implementation
    # can be switched using the appropriate feature flag.

    if dry_run:
        # Dry run mode, doe not create feedback but make a dummy link for email preview
        positive_feedback_url = f'{settings.FRONTEND_URL}/kto/ja/00000000-0000-0000-0000-000000000000'
        negative_feedback_url = f'{settings.FRONTEND_URL}/kto/nee/00000000-0000-0000-0000-000000000000'
    else:
        if ('API_USE_QUESTIONNAIRES_APP_FOR_FEEDBACK' in settings.FEATURE_FLAGS and
                settings.FEATURE_FLAGS['API_USE_QUESTIONNAIRES_APP_FOR_FEEDBACK']):
            session = create_session_for_feedback_request(signal)
            positive_feedback_url, negative_feedback_url = get_feedback_urls(session)
        else:
            feedback = Feedback.actions.request_feedback(signal)
            positive_feedback_url, negative_feedback_url = get_feedback_urls_no_questionnaires(feedback)

    return {
        'negative_feedback_url': negative_feedback_url,
        'positive_feedback_url': positive_feedback_url,
    }


def create_reaction_request_and_mail_context(signal: Signal, dry_run: bool = False) -> dict:
    """
    Util function to create a question, questionnaire and prepared session for reaction request mails
    """
    if dry_run:
        # Dry run, create a URL for email preview
        return {'reaction_url': f'{settings.FRONTEND_URL}/incident/reactie/00000000-0000-0000-0000-000000000000'}

    session = create_session_for_reaction_request(signal)
    reaction_url = get_reaction_url(session)

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

# Pattern to recognize URL encoded characters in the signal text and text_extra
URL_ENCODED_CHARACTERS_PATTERN = re.compile(r'(%[\dA-Z]{2})', re.IGNORECASE)


def _cleanup_signal_text(text: str, dry_run: bool = False) -> str:
    """
    Cleanup the text of a signal by removing all URL's and URL encoded characters
    """
    max_iterations = 5  # For now 5 iterations should be enough to remove all URLs. This could be a setting if needed
    while (re.search(URL_ENCODED_CHARACTERS_PATTERN, text) and max_iterations > 0):
        # Convert all URL encoded characters to their original form
        text = unquote(text)
        max_iterations = max_iterations - 1

    if re.search(URL_ENCODED_CHARACTERS_PATTERN, text):
        # After looping X times there are still URL encoded characters in the text, raise an exception
        if dry_run:
            # Dry run enabled return the text as is
            return text
        raise URLEncodedCharsFoundInText()

    # Remove URLs from the text
    text = re.sub(URL_PATTERN, '', text)

    # This text is clean
    return text


def make_email_context(signal: Signal, additional_context: Optional[dict] = None, dry_run: bool = False) -> dict:
    """
    Makes a context dictionary containing all values needed for the email templates
    Can add additional context, but will make sure that none of the default values are overridden.
    """
    # Decode the text and text_area before removing any URL to make sure that urlencoded URLs are also removed.
    text = _cleanup_signal_text(signal.text, dry_run=dry_run)
    text_extra = _cleanup_signal_text(signal.text_extra, dry_run=dry_run)

    category = signal.category_assignment.category
    context = {
        'signal_id': signal.id,
        'formatted_signal_id': signal.sia_id,
        'created_at': signal.created_at,
        'text': text,
        'text_extra': text_extra,
        'address': signal.location.address if signal.location and signal.location.address else None,
        'status_text': signal.status.text,
        'status_state': signal.status.state,
        'handling_message': signal.category_assignment.stored_handling_message,
        'ORGANIZATION_NAME': settings.ORGANIZATION_NAME,
        'main_category_name': category.parent.name if category.parent else '',
        'sub_category_name': category.name,
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
    Used to validate a template string with a dummy context
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


def markdownx_md(value: str) -> str:
    """
    Util function for the markdownx Django Admin preview functionality to make sure it is rendered with Mistune
    """
    render_markdown = create_markdown(escape=True)
    return render_markdown(value)


def trigger_mail_action_for_email_preview(signal, status_data):
    """
    Helper function that will check which mail action will be triggered if a new status is requested.
    """
    from signals.apps.email_integrations.services import MailService

    # Create the "new" status we want to use to trigger the mail
    status = Status(_signal=signal, **status_data)
    status.full_clean()
    status.id = 0  # Fake id so that we still can trigger the action rule

    subject = message = html_message = None
    for action in MailService.actions:
        # Execute the rule associated with the action
        if action.rule.validate(signal, status):
            # action found now render the subject, message and html_message and break the loop
            email_context = action.get_context(signal, dry_run=True)

            # overwrite the status context
            email_context.update({
                'status_text': status_data['text'],  # overwrite the status text
                'status_state': status_data['state'],  # overwrite the status state
                'afhandelings_text': status_data['text'],  # overwrite for the 'optional' action
                'reaction_request_answer': status_data['text'],  # overwrite for the 'reaction received' action
            })

            subject, message, html_message = action.render_mail_data(context=email_context)
            break

    return subject, message, html_message
