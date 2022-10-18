# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from email.utils import formataddr
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template, loader

from signals.apps.email_integrations.actions.abstract import AbstractSystemAction
from signals.apps.email_integrations.exceptions import URLEncodedCharsFoundInText
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.utils import make_email_context
from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)


class AssignedAction(AbstractSystemAction):
    """
    This e-mail action is triggered when a signal is assigned to a
    user or the users' department
    """

    key = EmailTemplate.SIGNAL_ASSIGNED
    subject = 'Melding aan jou toegewezen: {formatted_signal_id}'
    note = None

    def __call__(self, signal, dry_run=False, recipient=None):
        if self.rule(signal):
            if dry_run:
                return True

            if self.send_mail(signal, recipient=recipient):
                self.add_note(signal)
                return True

        return False

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

            subject = self.subject.format(formatted_signal_id=context['formatted_signal_id'])
            message = loader.get_template('email/assigned_default.txt').render(context)
            html_message = loader.get_template('email/assigned_default.html').render(context)

        return subject, message, html_message

    def get_context(self, signal, dry_run=False, recipient=None):
        """
        Email context
        """
        context = make_email_context(signal, self.get_additional_context(signal, dry_run, recipient), dry_run)
        return context

    def get_additional_context(self, signal, dry_run=False, recipient=None):
        return {
            'signal_url': f'{settings.FRONTEND_URL}/manage/{signal.id}',
            'recipient_full_name': recipient.get_full_name()
        }

    def send_mail(self, signal, dry_run=False, recipient=None):
        """
        Send the email to the reporter
        """
        try:
            context = self.get_context(signal, dry_run, recipient)
        except URLEncodedCharsFoundInText:
            # Log a warning and add a note  to the Signal that the email could not be sent
            logger.warning(f'URL encoded text found in Signal {signal.id}')
            Signal.actions.create_note(
                {'text':
                 'E-mail is niet verzonden omdat er verdachte tekens in de meldtekst staan.'},
                signal=signal
            )
            return 0  # No mail sent, return 0. Same behaviour as send_mail()
        subject, message, html_message = self.render_mail_data(context)

        recipient_list = [
            formataddr((recipient.get_full_name(), recipient.email))
        ]

        return send_mail(subject=subject, message=message, from_email=self.from_email,
                         recipient_list=recipient_list, html_message=html_message)
