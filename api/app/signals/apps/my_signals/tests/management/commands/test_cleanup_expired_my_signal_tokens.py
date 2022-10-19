# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import now
from freezegun import freeze_time

from signals.apps.my_signals.factories import TokenFactory
from signals.apps.my_signals.models import Token


class TestCleanupExpiredMySignalTokens(TestCase):
    def test_cleanup_task(self):
        """
        Only invalid tokens
        """
        with freeze_time(now() - timedelta(hours=24)):
            TokenFactory.create_batch(10)

        self.assertEqual(10, Token.objects.count())

        buffer = StringIO()
        call_command('cleanup_expired_my_signal_tokens', stdout=buffer)
        output = buffer.getvalue()

        self.assertIn('Deleted expired tokens', output)
        self.assertEqual(0, Token.objects.count())

    def test_cleanup_task_mixed_tokens(self):
        """
        Mixed valid and invalid tokens
        """
        with freeze_time(now() - timedelta(hours=24)):
            tokens_to_cleanup = TokenFactory.create_batch(5)

        tokens_to_cleanup_keys = [token.key for token in tokens_to_cleanup]

        with freeze_time(now() - timedelta(hours=1)):
            TokenFactory.create_batch(5)

        self.assertEqual(10, Token.objects.count())

        buffer = StringIO()
        call_command('cleanup_expired_my_signal_tokens', stdout=buffer)
        output = buffer.getvalue()

        self.assertIn('Deleted expired tokens', output)
        self.assertEqual(5, Token.objects.count())
        self.assertEqual(0, Token.objects.filter(key__in=tokens_to_cleanup_keys).count())
