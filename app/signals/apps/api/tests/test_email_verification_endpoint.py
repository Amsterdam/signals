# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import datetime
import typing

from django.utils import timezone

from signals.apps.email_integrations.factories import EmailTemplateFactory
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.signals.factories import ReporterFactory
from signals.apps.signals.models import Reporter
from signals.test.utils import SignalsBaseApiTestCase


class TestEmailVerificationEndpoint(SignalsBaseApiTestCase):
    PATH: typing.Final[str] = '/signals/v1/public/reporter/verify-email'
    TOKEN: typing.Final[str] = 'some_random_token_string'

    def test_token_does_not_exist(self):
        response = self.client.post(self.PATH, {'token': 'abc'}, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual({'token': ['Token not found!']}, response.json())

    def test_token_is_expired(self):
        year_ago = timezone.now() - datetime.timedelta(weeks=52)
        ReporterFactory.create(
            email_verification_token=self.TOKEN,
            email_verification_token_expires=year_ago,
        )

        response = self.client.post(self.PATH, {'token': self.TOKEN}, format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual({'token': ['Token expired!']}, response.json())

    def test_token_is_valid(self):
        EmailTemplateFactory.create(key=EmailTemplate.CONFIRM_REPORTER_UPDATED)
        original = ReporterFactory.create(state=Reporter.REPORTER_STATE_APPROVED, email='a@b.com', phone='123')
        signal = original._signal
        signal.reporter = original
        signal.save()

        ReporterFactory.create(
            email='b@c.nl',
            phone='456',
            state=Reporter.REPORTER_STATE_VERIFICATION_EMAIL_SENT,
            email_verification_token=self.TOKEN,
            email_verification_token_expires=timezone.now() + datetime.timedelta(weeks=1),
            _signal=signal,
        )

        response = self.client.post(self.PATH, {'token': self.TOKEN}, format='json')

        self.assertEqual(200, response.status_code)
        self.assertEqual({'token': self.TOKEN}, response.json())
