# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import typing
from unittest.mock import Mock

from django.conf import settings
from django.test import TestCase

from signals.apps.email_integrations.email_verification.reporter_verification import (
    ReporterVerifier
)
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.signals.factories import ReporterFactory


class TestReporterVerifier(TestCase):
    TOKEN: typing.Final[str] = 'token'

    def test_send_verification_mail(self):
        mailer = Mock()
        token_generator = Mock(return_value=self.TOKEN)

        reporter_verifier = ReporterVerifier(mailer, token_generator)

        reporter = ReporterFactory.create(email_verification_token=None, email_verification_token_expires=None, )

        reporter_verifier(reporter)

        token_generator.assert_called_once()
        mailer.assert_called_once_with(
            reporter,
            EmailTemplate.VERIFY_EMAIL_REPORTER,
            {'verification_url': f'{settings.FRONTEND_URL}/verify_email/{self.TOKEN}'}
        )
        self.assertEqual(reporter.email_verification_token, self.TOKEN)
        self.assertFalse(reporter.email_verified)
        self.assertIsNotNone(reporter.email_verification_token_expires)
