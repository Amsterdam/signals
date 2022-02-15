# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import re
from typing import Optional
from urllib.parse import unquote

from django.conf import settings
from django.core.validators import URLValidator
from django.db.transaction import atomic, savepoint, savepoint_rollback
from django.template import Context, Template
from django.utils.timezone import now
from mistune import create_markdown

from signals.apps.email_integrations.admin import EmailTemplate
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


def create_feedback_and_mail_context(signal: Signal) -> dict:
    """
    Util functions to create the feedback object and create the context needed for the mail
    """
    # Note: While the questionnaires app support for feedback requests is under
    # development we support both the "new" flow and the "old". Implementation
    # can be switched using the appropriate feature flag.

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


def create_reaction_request_and_mail_context(signal: Signal) -> dict:
    """
    Util function to create a question, questionnaire and prepared session for reaction request mails
    """
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


def make_email_context(signal: Signal, additional_context: Optional[dict] = None) -> dict:
    """
    Makes a context dictionary containing all values needed for the email templates
    Can add additional context, but will make sure that none of the default values are overridden.

    For backwards compatibility the Signal and the Status are still added to the context
    """
    # Decode the text and text_area before removing any URL to make sure that urlencoded URL's are also removed.
    text = re.sub(URL_PATTERN, '', unquote(signal.text))
    text_extra = re.sub(URL_PATTERN, '', unquote(signal.text_extra))

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


def trigger_mail_action_for_email_preview_and_rollback_all_changes(signal, status_data):
    """
    Helper function that will check which mail action will be triggered if a new status is set.

    To make use of the existing MailService we need to set the "new" status on the Signal and trigger the MailService
    with the dry_run flag set to True.

    All changes in the database will be rollbacked!!!
    """
    from signals.apps.email_integrations.services import MailService

    with atomic():
        # Create a savepoint to rollback to after the mail action has been triggered\
        sid = savepoint()

        try:
            # Create the "new" status we want to use to trigger the mail
            status = Status(_signal=signal, **status_data)
            status.full_clean()
            status.save()

            # Set the status, this will be rollbacked
            signal.status = status
            signal.save()

            subject = message = html_message = None
            for action in MailService.actions:
                if action(signal, dry_run=True):
                    # action found now render the subject, message and html_message and break the loop
                    subject, message, html_message = action.render_mail_data(action.get_context(signal))
                    break

            return subject, message, html_message
        finally:
            # Rollback to the created savepoint
            savepoint_rollback(sid)
