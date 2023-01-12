# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from unittest import mock

from django.test import TestCase

from signals.apps.email_integrations import tasks
from signals.apps.signals import workflow
from signals.apps.signals.factories import DepartmentFactory, SignalFactory, StatusFactory
from signals.apps.users.factories import UserFactory


class TestTasks(TestCase):
    @mock.patch('signals.apps.email_integrations.tasks.MailService.status_mail', autospec=True)
    def test_send_mail_reporter_created(self, mocked_mail):
        signal = SignalFactory.create()
        signal.status = StatusFactory(_signal=signal, state=workflow.BEHANDELING)
        signal.save()

        tasks.send_mail_reporter(pk=signal.pk)
        mocked_mail.assert_called_once_with(signal=signal.pk)

    @mock.patch('signals.apps.email_integrations.tasks.MailService.system_mail', autospec=True)
    def test_send_mail_assigned_signal_departments(self, mocked_mail):
        signal = SignalFactory.create()
        department = DepartmentFactory.create()

        user_with_notification = UserFactory.create()
        user_with_notification.profile.notification_on_department_assignment = True
        user_with_notification.profile.save()
        user_with_notification.profile.departments.add(department)

        user_without_notification = UserFactory.create()
        user_without_notification.profile.notification_on_department_assignment = False
        user_without_notification.profile.save()
        user_without_notification.profile.departments.add(department)

        tasks.send_mail_assigned_signal_departments(signal_pk=signal.pk, department_pks=[department.pk])

        mocked_mail.assert_called_once_with(
            signal=signal,
            action_name='assigned',
            recipient=user_with_notification,
            assigned_to=department
        )

    @mock.patch('signals.apps.email_integrations.tasks.MailService.system_mail', autospec=True)
    def test_send_mail_assigned_signal_user(self, mocked_mail):
        signal = SignalFactory.create()

        user_with_notification = UserFactory.create()
        user_with_notification.profile.notification_on_user_assignment = True
        user_with_notification.profile.save()

        user_without_notification = UserFactory.create()

        inactive_user = UserFactory.create(is_active=False)
        inactive_user.profile.notification_on_user_assignment = True
        inactive_user.profile.save()

        tasks.send_mail_assigned_signal_user(signal_pk=signal.pk, user_pk=user_with_notification.pk)
        tasks.send_mail_assigned_signal_user(signal_pk=signal.pk, user_pk=user_without_notification.pk)
        tasks.send_mail_assigned_signal_user(signal_pk=signal.pk, user_pk=inactive_user.pk)

        mocked_mail.assert_called_once_with(
            signal=signal,
            action_name='assigned',
            recipient=user_with_notification,
            assigned_to=user_with_notification
        )
