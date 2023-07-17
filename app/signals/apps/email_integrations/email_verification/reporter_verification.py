# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from signals.apps.email_integrations.email_verification.reporter_mailer import ReporterMailer
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.signals.models import Reporter
from signals.apps.signals.tokens.token_generator import TokenGenerator


class ReporterVerifier:
    """This class attempts to send a verification email to a reporter.
    The verification email contains a link that can be clicked by the reporter to verify their
    email address."""
    _mail: ReporterMailer
    _generate_token: TokenGenerator

    def __init__(self, mailer: ReporterMailer, token_generator: TokenGenerator):
        self._mail = mailer
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
        token = self._generate_token()

        reporter.email_verification_token = token
        reporter.email_verified = False
        reporter.email_verification_token_expires = timezone.now() + timedelta(
            hours=settings.EMAIL_VERIFICATION_TOKEN_HOURS_VALID
        )
        reporter.save()

        context = {
            'verification_url': f'{settings.FRONTEND_URL}/verify_email/{token}',
        }

        self._mail(reporter, EmailTemplate.VERIFY_EMAIL_REPORTER, context)
