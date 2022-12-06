# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Delta10 B.V.
import logging
from email.utils import formataddr

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template import Context, Template, loader

from signals.apps.email_integrations.actions.abstract import AbstractSystemAction
from signals.apps.email_integrations.exceptions import URLEncodedCharsFoundInText
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.signals.models import Department

logger = logging.getLogger(__name__)

User = get_user_model()


class AssignedAction(AbstractSystemAction):
    """
    This e-mail action is triggered when a signal is assigned to a
    user or the users' department
    """

    _required_call_kwargs = ('recipient', 'assigned_to')

    key = EmailTemplate.SIGNAL_ASSIGNED
    subject = (
        "Melding {{ formatted_signal_id }} is toegewezen aan "
        "{% if assigned_to_user %}jou{% else %}{{ assigned_to_department }}{% endif %}"
    )

    note = None

    def get_additional_context(self, signal, dry_run=False):
        recipient = self.kwargs['recipient']
        assigned_to = self.kwargs['assigned_to']

        return {
            'signal_url': f'{settings.FRONTEND_URL}/manage/incident/{signal.id}',
            'recipient_full_name': recipient.get_full_name(),
            'assigned_to_user': assigned_to if isinstance(assigned_to, User) else None,
            'assigned_to_department': assigned_to if isinstance(assigned_to, Department) else None
        }

    def get_recipient_list(self, signal):
        return [
            formataddr((self.kwargs['recipient'].get_full_name(), self.kwargs['recipient'].email))
        ]

    def render_mail_data(self, context):
        """
        Renders the subject, text message body and html message body
        """
        try:
            email_template = EmailTemplate.objects.get(key=self.key)

            rendered_context = {
                'subject': Template(email_template.title).render(Context(context)),
                'body': Template(email_template.body).render(Context(context, autoescape=False))
            }

            subject = Template(email_template.title).render(Context(context, autoescape=False))
            message = loader.get_template('email/_base.txt').render(rendered_context)
            html_message = loader.get_template('email/_base.html').render(rendered_context)
        except EmailTemplate.DoesNotExist:
            logger.warning(f'EmailTemplate {self.key} does not exists')

            subject = Template(self.subject).render(Context(context, autoescape=False))
            message = loader.get_template('email/assigned_default.txt').render(context)
            html_message = loader.get_template('email/assigned_default.html').render(context)

        return subject, message, html_message

    def send_mail(self, signal, dry_run=False):
        """
        Send the email to the reporter
        """
        try:
            context = self.get_context(signal, dry_run)
        except URLEncodedCharsFoundInText:
            # Log a warning that the email could not be sent
            logger.warning(f'URL encoded text found in Signal {signal.id}')
            return 0  # No mail sent, return 0. Same behaviour as send_mail()

        subject, message, html_message = self.render_mail_data(context)

        return send_mail(subject=subject, message=message, from_email=self.from_email,
                         recipient_list=self.get_recipient_list(signal), html_message=html_message)
