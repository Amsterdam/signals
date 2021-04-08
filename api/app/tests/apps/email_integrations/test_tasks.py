# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from unittest import mock

from django.test import TestCase

from signals.apps.email_integrations import tasks
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory


class TestTasks(TestCase):
    signal = None

    def setUp(self):
        self.signal = SignalFactory.create()
        self.prev_status = self.signal.status
        self.signal.status = StatusFactory(_signal=self.signal, state=workflow.BEHANDELING)
        self.signal.save()

    @mock.patch('signals.apps.email_integrations.tasks.MailActions', autospec=True)
    def test_send_mail_reporter_created(self, mocked_mail):
        tasks.send_mail_reporter(pk=self.signal.id)
        mocked_mail().apply.assert_called_once_with(self.signal.pk)
