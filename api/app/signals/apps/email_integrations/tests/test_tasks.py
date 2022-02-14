# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from unittest import mock

from django.test import TestCase

from signals.apps.email_integrations import tasks
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory


class TestTasks(TestCase):
    @mock.patch('signals.apps.email_integrations.tasks.MailService.mail', autospec=True)
    def test_send_mail_reporter_created(self, mocked_mail):
        signal = SignalFactory.create()
        signal.status = StatusFactory(_signal=signal, state=workflow.BEHANDELING)
        signal.save()

        tasks.send_mail_reporter(pk=signal.pk)
        mocked_mail.assert_called_once_with(signal=signal.pk)
