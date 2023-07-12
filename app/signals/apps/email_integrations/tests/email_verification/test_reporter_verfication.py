# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import typing
from unittest.mock import MagicMock, Mock, patch

import pytest

from signals.apps.email_integrations.email_verification.reporter_verification import (
    FailedToSendVerificationMailException,
    ReporterVerifier
)
from signals.apps.signals.models import Reporter


class TestReporterVerifier:
    FROM_EMAIL: typing.Final[str] = 'noreply@example.com'
    EMAIL: typing.Final[str] = 'someone@example.com'
    SUBJECT: typing.Final[str] = 'subject'
    MESSAGE: typing.Final[str] = 'message'
    HTML_MESSAGE: typing.Final[str] = 'html_message'

    @patch('signals.apps.signals.email_verification.reporter_verification.send_mail')
    def test_send_verification_mail(self, send_mail: MagicMock):
        send_mail.return_value = 1
        renderer = Mock(return_value=(self.SUBJECT, self.MESSAGE, self.HTML_MESSAGE))
        token_generator = Mock()
        reporter_verifier = ReporterVerifier(renderer, token_generator, self.FROM_EMAIL)

        reporter = Reporter()
        reporter.email = self.EMAIL

        reporter_verifier(reporter)

        token_generator.assert_called_once()
        renderer.assert_called_once()
        send_mail.assert_called_once_with(
            from_email=self.FROM_EMAIL,
            recipient_list=[self.EMAIL],
            subject=self.SUBJECT,
            message=self.MESSAGE,
            html_message=self.HTML_MESSAGE,
        )

    def test_raises_exception_when_reporter_has_no_email(self):
        renderer = Mock(return_value=(self.SUBJECT, self.MESSAGE, self.HTML_MESSAGE))
        token_generator = Mock()
        reporter_verifier = ReporterVerifier(renderer, token_generator)

        with pytest.raises(FailedToSendVerificationMailException) as e_info:
            reporter_verifier(Reporter())

        assert str(e_info.value) == 'Reporter has no email address!'
