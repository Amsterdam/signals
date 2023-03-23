# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.db import IntegrityError
from django.test import TestCase

from signals.apps.email_integrations.models import EmailTemplate


class TestEmailTemplate(TestCase):
    def test_bug_email_template_key_must_be_unique(self):
        """
        Per "key" only 1 EmailTemplate can exist, test that adding a duplicate
        key will raise the appropriate IntegrityError
        """
        EmailTemplate.objects.create(
            key=EmailTemplate.SIGNAL_CREATED,
            title='test',
            body='test',
            created_by='test@test.com',
        )
        with self.assertRaises(IntegrityError) as ie:
            EmailTemplate.objects.create(
                key=EmailTemplate.SIGNAL_CREATED,
                title='test',
                body='test',
                created_by='test@test.com',
            )

        self.assertIn('duplicate key value violates unique constraint',
                      str(ie.exception))
