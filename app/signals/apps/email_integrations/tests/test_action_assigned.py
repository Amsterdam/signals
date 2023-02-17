# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Delta10 B.V.
from django.conf import settings
from django.core import mail
from django.test import TestCase

from signals.apps.email_integrations.services import MailService
from signals.apps.signals.factories import DepartmentFactory, SignalFactory
from signals.apps.users.factories import UserFactory


class TestActionAssigned(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create()
        self.user = UserFactory.create()
        self.department = DepartmentFactory.create()

    def test_mail_assigned_to_user(self):
        MailService.system_mail(
                signal=self.signal,
                action_name='assigned',
                recipient=self.user,
                assigned_to=self.user
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Melding {self.signal.get_id_display()} is toegewezen aan jou')
        self.assertEqual(mail.outbox[0].to, [f'{self.user.get_full_name()} <{self.user.email}>'])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)

    def test_mail_assigned_to_department(self):
        self.assertEqual(len(mail.outbox), 0)

        MailService.system_mail(
                signal=self.signal,
                action_name='assigned',
                recipient=self.user,
                assigned_to=self.department
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         f'Melding {self.signal.get_id_display()} is toegewezen aan {self.department}'
                         )
        self.assertEqual(mail.outbox[0].to, [f'{self.user.get_full_name()} <{self.user.email}>'])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
