# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now
from freezegun import freeze_time

from signals.apps.my_signals.factories import TokenFactory
from signals.apps.my_signals.models import Token
from signals.apps.my_signals.tasks import delete_expired_tokens


class TestCleanupTask(TestCase):
    def test_cleanup_task(self):
        """
        Only invalid tokens
        """
        with freeze_time(now() - timedelta(hours=24)):
            TokenFactory.create_batch(10)

        self.assertEqual(10, Token.objects.count())
        delete_expired_tokens()
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
        delete_expired_tokens()
        self.assertEqual(5, Token.objects.count())
        self.assertEqual(0, Token.objects.filter(key__in=tokens_to_cleanup_keys).count())
