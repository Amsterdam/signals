# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.my_signals.app_settings import MY_SIGNALS_LOGIN_URL
from signals.apps.my_signals.models import Token
from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Signal


class TestObtainMySignalsTokenEndpoint(APITestCase):
    endpoint = '/signals/v1/my/signals/request-auth-token'

    def setUp(self):
        EmailTemplate.objects.create(key=EmailTemplate.MY_SIGNAL_TOKEN, title='Uw login token', body='{{ login_url }}')

    def test_request_token_no_signals(self):
        """
        No Signals in the database should not create a token and send an email
        """
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(0, Signal.objects.count())
        self.assertEqual(0, Token.objects.count())

        response = self.client.post(f'{self.endpoint}', data={'email': 'doesnotexists@example.com'}, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(0, Token.objects.count())
        self.assertEqual(len(mail.outbox), 0)

    def test_request_token_no_signals_for_reporter(self):
        """
        No Signals for the reporter in the database should not create a token and send an email
        """
        SignalFactory.create_batch(10, reporter__email='reporter@example.com')

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(10, Signal.objects.count())
        self.assertEqual(0, Token.objects.count())

        response = self.client.post(f'{self.endpoint}', data={'email': 'doesnotexists@example.com'}, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(0, Token.objects.count())
        self.assertEqual(len(mail.outbox), 0)

    def test_request_token_signals_for_reporter_created_more_than_12_months_ago(self):
        """
        Signals created more than 12 months ago for the reporter in the database should not create a token and send an
        email
        """
        with freeze_time(now() - timedelta(days=366)):
            SignalFactory.create_batch(10, reporter__email='reporter@example.com')

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(10, Signal.objects.count())
        self.assertEqual(0, Token.objects.count())

        response = self.client.post(f'{self.endpoint}', data={'email': 'doesnotexists@example.com'}, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(0, Token.objects.count())
        self.assertEqual(len(mail.outbox), 0)

    def test_request_token(self):
        """
        """
        with freeze_time(now() - timedelta(days=10)):
            SignalFactory.create(reporter__email='reporter@example.com')

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(1, Signal.objects.count())
        self.assertEqual(0, Token.objects.count())

        response = self.client.post(f'{self.endpoint}', data={'email': 'reporter@example.com'}, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(1, Token.objects.count())

        token = Token.objects.get(reporter_email='reporter@example.com')
        self.assertEqual('reporter@example.com', token.reporter_email)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Uw login token')
        self.assertEqual(mail.outbox[0].to, ['reporter@example.com', ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn(f'{MY_SIGNALS_LOGIN_URL}/{token.key}', mail.outbox[0].body)
