# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import typing
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.test import override_settings

from signals.apps.email_integrations.email_verification.reporter_mailer import (
    FailedToSendReporterMailException,
    ReporterMailer
)
from signals.apps.signals.models import Reporter


class TestReporterMailer:
    FROM_EMAIL: typing.Final[str] = 'noreply@example.com'
    EMAIL: typing.Final[str] = 'someone@example.com'
    SUBJECT: typing.Final[str] = 'subject'
    MESSAGE: typing.Final[str] = 'message'
    HTML_MESSAGE: typing.Final[str] = 'html_message'
    TEMPLATE_KEY: typing.Final[str] = 'template_key'
    ORGANIZATION_NAME: typing.Final[str] = 'De gemeente'

    @patch('signals.apps.email_integrations.email_verification.reporter_mailer.send_mail')
    def test_send_verification_mail(self, send_mail: MagicMock):
        send_mail.return_value = 1
        renderer = Mock(return_value=(self.SUBJECT, self.MESSAGE, self.HTML_MESSAGE))
        mailer = ReporterMailer(renderer, self.FROM_EMAIL)

        reporter = Reporter()
        reporter.email = self.EMAIL

        with override_settings(ORGANIZATION_NAME=self.ORGANIZATION_NAME):
            mailer(reporter, self.TEMPLATE_KEY)

        renderer.assert_called_once_with(self.TEMPLATE_KEY, {'ORGANIZATION_NAME': self.ORGANIZATION_NAME})
        send_mail.assert_called_once_with(
            from_email=self.FROM_EMAIL,
            recipient_list=[self.EMAIL],
            subject=self.SUBJECT,
            message=self.MESSAGE,
            html_message=self.HTML_MESSAGE,
        )

    def test_raises_exception_when_reporter_has_no_email(self):
        renderer = Mock(return_value=(self.SUBJECT, self.MESSAGE, self.HTML_MESSAGE))
        mailer = ReporterMailer(renderer, self.FROM_EMAIL)

        with pytest.raises(FailedToSendReporterMailException) as e_info:
            mailer(Reporter(), self.TEMPLATE_KEY)

        assert str(e_info.value) == 'Reporter has no email address!'
