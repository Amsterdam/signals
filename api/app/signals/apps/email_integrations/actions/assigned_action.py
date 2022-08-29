# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template, loader

from signals.apps.email_integrations.exceptions import URLEncodedCharsFoundInText
from signals.apps.email_integrations.actions.abstract import AbstractSystemAction
from signals.apps.email_integrations.models import EmailTemplate

logger = logging.getLogger(__name__)


class AssignedAction(AbstractSystemAction):
    key = EmailTemplate.SIGNAL_ASSIGNED
    subject = 'Melding aan jou toegewezen: {formatted_signal_id}'
    note = 'Automatische e-mail.'

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

    def get_additional_context(self, signal, dry_run=False):
        return {
            'signal_url': f'{settings.FRONTEND_URL}/manage/{signal.id}',
        }
