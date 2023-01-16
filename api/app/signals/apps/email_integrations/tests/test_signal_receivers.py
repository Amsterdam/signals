# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Delta10 B.V.
from unittest import mock

from django.test import TestCase

from signals.apps.signals.factories import (
    DepartmentFactory,
    SignalDepartmentsFactory,
    SignalFactory,
    SignalUserFactory
)
from signals.apps.signals.managers import update_signal_departments, update_user_assignment
from signals.apps.signals.models import SignalDepartments


class TestDepartmentSignalReceivers(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create()
        self.department = DepartmentFactory.create()
        self.signal_departments = SignalDepartmentsFactory.create(
            _signal=self.signal,
            relation_type=SignalDepartments.REL_ROUTING,
            departments=[self.department]
        )

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_update_signal_departments_handler(self, mocked_tasks):
        update_signal_departments.send_robust(
            sender=self.__class__,
            signal_obj=self.signal,
            signal_departments=self.signal_departments,
            prev_signal_departments=SignalDepartments.objects.none()
        )

        mocked_tasks.send_mail_assigned_signal_departments.delay.assert_called_once_with(
            signal_pk=self.signal.id,
            department_pks=[self.department.pk]
        )

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_unchanged_update_signal_departments_handler(self, mocked_tasks):
        update_signal_departments.send_robust(
            sender=self.__class__,
            signal_obj=self.signal,
            signal_departments=self.signal_departments,
            prev_signal_departments=self.signal_departments
        )

        mocked_tasks.send_mail_assigned_signal_departments.delay.assert_not_called()


class TestUserSignalReceivers(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create()
        self.signal_user = SignalUserFactory.create()

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_update_user_assignment_handler(self, mocked_tasks):
        update_user_assignment.send_robust(
            sender=self.__class__,
            signal_obj=self.signal,
            user_assignment=self.signal_user,
            prev_user_assignment=None
        )

        mocked_tasks.send_mail_assigned_signal_user.delay.assert_called_once_with(
            signal_pk=self.signal.id,
            user_pk=self.signal_user.user.pk
        )

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_unchanged_update_user_assignment_handler(self, mocked_tasks):
        update_user_assignment.send_robust(
            sender=self.__class__,
            signal_obj=self.signal,
            user_assignment=self.signal_user,
            prev_user_assignment=self.signal_user
        )

        mocked_tasks.send_mail_assigned_signal_user.delay.assert_not_called()
