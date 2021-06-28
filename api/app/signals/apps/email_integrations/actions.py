# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import logging
from abc import ABC

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template, loader

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.rules import (
    SignalCreatedRule,
    SignalHandledRule,
    SignalOptionalRule,
    SignalReopenedRule,
    SignalScheduledRule
)
from signals.apps.email_integrations.utils import (
    _create_feedback_and_mail_context,
    make_email_context
)
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


class SignalCreatedAction(AbstractAction):
    rule = SignalCreatedRule()

    key = EmailTemplate.SIGNAL_CREATED
    subject = 'Bedankt voor uw melding {signal_id}'

    note = 'Automatische e-mail bij registratie van de melding is verzonden aan de melder.'

    def get_additional_context(self, signal):
        return {
            'afhandelings_text': signal.category_assignment.category.handling_message
        }


class SignalHandledAction(AbstractAction):
    rule = SignalHandledRule()

    key = EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD
    subject = 'Meer over uw melding {signal_id}'

    note = 'Automatische e-mail bij afhandelen is verzonden aan de melder.'

    def get_additional_context(self, signal):
        return _create_feedback_and_mail_context(signal)


class SignalScheduledAction(AbstractAction):
    rule = SignalScheduledRule()

    key = EmailTemplate.SIGNAL_STATUS_CHANGED_INGEPLAND
    subject = 'Meer over uw melding {signal_id}'

    note = 'Automatische e-mail bij inplannen is verzonden aan de melder.'


class SignalReopenedAction(AbstractAction):
    rule = SignalReopenedRule()

    key = EmailTemplate.SIGNAL_STATUS_CHANGED_HEROPEND
    subject = 'Meer over uw melding {signal_id}'

    note = 'Automatische e-mail bij heropenen is verzonden aan de melder.'


class SignalOptionalAction(AbstractAction):
    rule = SignalOptionalRule()

    key = EmailTemplate.SIGNAL_STATUS_CHANGED_OPTIONAL
    subject = 'Meer over uw melding {signal_id}'

    note = 'De statusupdate is per e-mail verzonden aan de melder'

    def get_additional_context(self, signal):
        return {
            'afhandelings_text': signal.status.text
        }
