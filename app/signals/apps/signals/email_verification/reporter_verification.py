# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.core.mail import send_mail

from signals import settings
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.renderers.email_template_renderer import EmailTemplateRenderer
from signals.apps.signals.models import Reporter
from signals.apps.signals.tokens.token_generator import TokenGenerator


class FailedToSendVerificationMailException(Exception):
    """This exception is raised when there is a failure with sending the verification email."""


class ReporterVerifier:
    """This class attempts to send a verification email to a reporter.
    The verification email contains a link that can be clicked by the reporter to verify their
    email address."""
    _render_email_template: EmailTemplateRenderer
    _generate_token: TokenGenerator

    def __init__(
            self,
            email_template_renderer: EmailTemplateRenderer,
            token_generator: TokenGenerator
    ):
        self._render_email_template = email_template_renderer
        self._generate_token = token_generator

    def __call__(self, reporter: Reporter) -> None:
        """Sends the actual verification email or raises `FailedToSendVerificationMailException`
        if it is not possible to send the email.

        Parameters
        ----------
        reporter: Reporter
            The reporter to send the verification email to. Obviously the reporter needs to have
            an email address.
        """
        if not reporter.email:
            raise FailedToSendVerificationMailException('Reporter has no email address!')

        context = {
            'verification_url': f'{settings.FRONTEND_URL}/verify_email/{self._generate_token()}',
            'ORGANIZATION_NAME': settings.ORGANIZATION_NAME
        }
        subject, message, html_message = self._render_email_template(
            EmailTemplate.VERIFY_EMAIL_REPORTER,
            context
        )

        sent = send_mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reporter.email],
            subject=subject,
            message=message,
            html_message=html_message,
        ) > 0

        if not sent:
            raise FailedToSendVerificationMailException('Mail was not sent!')
