# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import copy
import logging
from typing import Any

from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.template import Context, Template, loader
from django.utils.text import slugify

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.utils import make_email_context
from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)


class MailActions:
    _from_email = settings.DEFAULT_FROM_EMAIL

    def __init__(self, mail_rules: list = []) -> None:
        self._conditions = {}
        self._kwargs = {}
        self._additional_info = {}

        for config in mail_rules:
            key = slugify(config['name'])

            self._conditions[key] = config['conditions'] if 'conditions' in config else {}
            self._kwargs[key] = config['kwargs'] if 'kwargs' in config else {}
            self._additional_info[key] = config['additional_info'] if 'additional_info' in config else {}

    def _apply_filters(self, filters: dict, signal: Signal) -> bool:
        try:
            Signal.objects.filter(**filters).get(pk=signal.pk)
            return True
        except Signal.DoesNotExist:
            pass
        return False

    def _apply_functions(self, functions: dict, signal: Signal) -> bool:
        return all([
            function(signal)
            for _, function in functions.items()
        ])

    def _apply_conditions(self, conditions: dict, signal: Signal) -> Any:
        filters = conditions['filters'] if 'filters' in conditions else {}
        functions = conditions['functions'] if 'functions' in conditions else {}

        return (self._apply_filters(filters=filters, signal=signal) and
                self._apply_functions(functions=functions, signal=signal))

    def _get_actions(self, signal: Signal) -> list:
        found_actions_to_apply = []
        for key, conditions in self._conditions.items():
            if self._apply_conditions(conditions=conditions, signal=signal):
                found_actions_to_apply.append(key)
        return found_actions_to_apply

    def _get_mail_context(self, signal: Signal, mail_kwargs: dict):
        additional_context = {}
        if 'context' in mail_kwargs and callable(mail_kwargs['context']):
            additional_context.update(mail_kwargs['context'](signal))

        return make_email_context(signal=signal, additional_context=additional_context)

    def _mail(self, signal: Signal, mail_kwargs: dict):
        context = self._get_mail_context(signal=signal, mail_kwargs=mail_kwargs)

        try:
            email_template = EmailTemplate.objects.get(key=mail_kwargs['key'])

            # do not escape as subject is not rendered as HTML
            subject = Template(email_template.title).render(Context(context, autoescape=False))

            rendered_context = {
                'subject': Template(email_template.title).render(Context(context)),

                # do not escape HTML as this is handled by Markdown filter
                'body': Template(email_template.body).render(Context(context, autoescape=False))
            }

            html_message = loader.get_template('email/_base.html').render(rendered_context)
            message = loader.get_template('email/_base.txt').render(rendered_context)
        except EmailTemplate.DoesNotExist:
            logger.warning(f'EmailTemplate {mail_kwargs["key"]} does not exists')

            # A mail needs to be sent, so if there is no template in the DB we sent a default simple e-mail message
            subject = mail_kwargs['subject'].format(signal_id=signal.id)
            message = loader.get_template('email/signal_default.txt').render(context)
            html_message = loader.get_template('email/signal_default.html').render(context)

        return django_send_mail(subject=subject, message=message, from_email=self._from_email,
                                recipient_list=[signal.reporter.email, ], html_message=html_message)

    def _add_note(self, signal: Signal, text: str) -> None:
        # Add a note to a given Signals history
        data = {'text': text}
        Signal.actions.create_note(data=data, signal=signal)

    def apply(self, signal_id: int, send_mail: bool = True) -> None:
        signal = Signal.objects.get(pk=signal_id)

        actions = self._get_actions(signal=signal)
        for action in actions:
            kwargs = copy.deepcopy(self._kwargs[action])
            history_entry_text = self._additional_info[action].get('history_entry_text', '')

            if send_mail:
                self._mail(signal=signal, mail_kwargs=kwargs)
                if history_entry_text:
                    self._add_note(signal=signal, text=history_entry_text)
