# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import logging
from abc import ABC

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template, loader

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.utils import make_email_context
from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)


class AbstractAction(ABC):
    rule = None

    key = None
    subject = None
    from_email = settings.DEFAULT_FROM_EMAIL

    note = None

    def __call__(self, signal, dry_run=False):
        if self.rule(signal):
            if dry_run:
                return True

            if self.mail(signal):
                self.add_note(signal)
            return True

        return False

    def get_additional_context(self, signal):
        return {}

    def get_context(self, signal):
        context = make_email_context(signal, self.get_additional_context(signal))
        return context

    def mail(self, signal):
        context = self.get_context(signal)

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

            subject = self.subject.format(signal_id=signal.id)
            message = loader.get_template('email/signal_default.txt').render(context)
            html_message = loader.get_template('email/signal_default.html').render(context)

        return send_mail(subject=subject, message=message, from_email=self.from_email,
                         recipient_list=[signal.reporter.email, ], html_message=html_message)

    def add_note(self, signal):
        Signal.actions.create_note({'text': self.note}, signal=signal)
