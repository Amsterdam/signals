# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.utils.timezone import now
from freezegun import freeze_time

from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.my_signals.app_settings import MY_SIGNALS_URL
from signals.apps.my_signals.factories import TokenFactory
from signals.apps.my_signals.mail import send_token_mail
from signals.apps.my_signals.models import Token


class TestMail(TestCase):
    def setUp(self):
        EmailTemplate.objects.create(key=EmailTemplate.MY_SIGNAL_TOKEN, title='Uw login token',
                                     body='{{ my_signals_url }}')

    def test_send_mail_valid_token(self):
        with freeze_time(now()):
            token = TokenFactory.create()

        self.assertEqual(1, Token.objects.count())

        send_token_mail(token)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Uw login token')
        self.assertEqual(mail.outbox[0].to, [token.reporter_email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn(f'{MY_SIGNALS_URL}/{token.key}', mail.outbox[0].body)

    def test_send_mail_invalid_token(self):
        with freeze_time(now() - timedelta(days=10)):
            token = TokenFactory.create()

        self.assertEqual(1, Token.objects.count())

        send_token_mail(token)

        self.assertEqual(len(mail.outbox), 0)
