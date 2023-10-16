# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
import logging
import typing
from abc import ABC, abstractmethod

from django.conf import settings
from django.core.mail import send_mail
from django.template import loader

from signals.apps.email_integrations.exceptions import URLEncodedCharsFoundInText
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.renderers.email_template_renderer import EmailTemplateRenderer
from signals.apps.email_integrations.rules.abstract import AbstractRule
from signals.apps.email_integrations.utils import make_email_context
from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)


class AbstractAction(ABC):
    """
    This class is used to define email action's.

    The derived class action must implement a custom Rule. For example the SignalCreatedAction uses the
    SignalCreatedRule to determine if it should trigger and send the Signal created email.
    """
    _render: EmailTemplateRenderer

    # The key of the email template. Is used to retrieve the corresponding EmailTemplate from the database
    # If there is no EmailTemplate with this key a fallback email template is used.
    # The fallback email templates:
    # - email/signal_default.txt
    # - email/signal_default.html)
    key: str

    # The subject of the email
    subject: str
    from_email: str = settings.DEFAULT_FROM_EMAIL

    # Body of email
    fallback_txt_template: str = 'email/signal_default.txt'
    fallback_html_template: str = 'email/signal_default.html'

    # Will be used to create a note on the Signal after the email has been sent
    note: typing.Optional[str] = None

    def __init__(self, renderer: EmailTemplateRenderer):
        self._render = renderer

    @abstractmethod
    def __call__(self, signal: Signal, dry_run: bool = False) -> bool:
        if dry_run:
            return True

        if self.send_mail(signal):
            self.add_note(signal)
            return True

        return False

    def get_additional_context(self, signal: Signal, dry_run: bool = False) -> dict:
        """
        Overwrite this function if additional email context is needed.
        """
        return {}

    def get_context(self, signal: Signal, dry_run: bool = False) -> dict:
        """
        Email context
        """
        context = make_email_context(signal, self.get_additional_context(signal, dry_run), dry_run)
        return context

    def get_recipient_list(self, signal: Signal) -> list[str]:
        """
        Email address, override if we do not want to mail the reporter
        """
        assert signal.reporter is not None
        assert signal.reporter.email is not None

        return [signal.reporter.email]

    def render_mail_data(self, context: dict) -> tuple[str, str, str]:
        """
        Renders the subject, text message body and html message body
        """
        try:
            return self._render(self.key, context)
        except EmailTemplate.DoesNotExist:
            logger.warning(f'EmailTemplate {self.key} does not exists')

            subject = self.subject.format(formatted_signal_id=context['formatted_signal_id'])
            message = loader.get_template(self.fallback_txt_template).render(context)
            html_message = loader.get_template(self.fallback_html_template).render(context)

        return subject, message, html_message

    def send_mail(self, signal: Signal, dry_run: bool = False) -> int:
        """
        Send the email to the reporter
        """
        try:
            context = self.get_context(signal, dry_run)
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
        return send_mail(subject=subject, message=message, from_email=self.from_email,
                         recipient_list=self.get_recipient_list(signal), html_message=html_message)

    def add_note(self, signal: Signal):
        if self.note:
            Signal.actions.create_note({'text': self.note}, signal=signal)


class AbstractSignalStatusAction(AbstractAction):
    rule: AbstractRule

    def __call__(self, signal: Signal, dry_run: bool = False) -> bool:
        if self.rule(signal):
            return super(AbstractSignalStatusAction, self).__call__(signal, dry_run)

        return False


class AbstractSystemAction(AbstractAction):
    _required_call_kwargs: list[str]
    kwargs = None

    def __call__(self, signal: Signal, dry_run: bool = False, **kwargs) -> bool:
        """
        check if the required parameters are in the kwargs
        """
        if self._required_call_kwargs and \
                not all(x in kwargs.keys() for x in self._required_call_kwargs):
            raise TypeError(f'{self.__class__.__name__} requires {self._required_call_kwargs}')

        self.kwargs = kwargs

        if self._validate():
            return super(AbstractSystemAction, self).__call__(signal=signal, dry_run=dry_run)

        return False

    def _validate(self) -> bool:
        return True
