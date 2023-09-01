# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.conf import settings
from django.core.mail import send_mail

from signals.apps.email_integrations.renderers.email_template_renderer import EmailTemplateRenderer
from signals.apps.email_integrations.utils import make_email_context
from signals.apps.signals.models import Reporter


class FailedToSendReporterMailException(Exception):
    """This exception is raised when there is a failure with sending the email."""


class ReporterMailer:
    """Email a reporter based on a template stored in the database"""
    from_email: str
    _render_email_template: EmailTemplateRenderer

    def __init__(
            self,
            email_template_renderer: EmailTemplateRenderer,
            from_email: str = settings.DEFAULT_FROM_EMAIL,
    ):
        self._render_email_template = email_template_renderer
        self.from_email = from_email

    def __call__(self, reporter: Reporter, template_key: str, context: dict = None) -> None:
        """Send the actual email.

        Parameters
        ----------
        reporter: Reporter
            The reporter to send the email to.
        template_key: str
            The key of the template that is stored in the database.
        context: dict
            The variables for the template.

        Returns
        -------
        None
        """
        if not reporter.email:
            raise FailedToSendReporterMailException('Reporter has no email address!')

        context = make_email_context(reporter._signal, context)

        subject, message, html_message = self._render_email_template(
            template_key,
            context
        )

        send_mail(
            from_email=self.from_email,
            recipient_list=[reporter.email],
            subject=subject,
            message=message,
            html_message=html_message,
        )
