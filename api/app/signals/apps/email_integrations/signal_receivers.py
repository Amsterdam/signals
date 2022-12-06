# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.email_integrations import tasks
from signals.apps.signals.managers import (
    create_initial,
    update_signal_departments,
    update_status,
    update_user_assignment
)


@receiver((create_initial, update_status), dispatch_uid='core_email_integrations_update_status')
def update_status_handler(sender, signal_obj, *args, **kwargs):
    tasks.send_mail_reporter.delay(pk=signal_obj.pk)


@receiver(update_signal_departments, dispatch_uid='core_email_integrations_update_signal_departments')
def update_signal_departments_handler(sender, signal_obj, signal_departments, prev_signal_departments, *args, **kwargs):
    if signal_departments and prev_signal_departments:
        if set(signal_departments.departments.all()) == set(prev_signal_departments.departments.all()):
            return  # do not trigger when the departments field is unchanged

    department_pks = [department.pk for department in signal_departments.departments.all()]

    tasks.send_mail_assigned_signal_departments.delay(
        signal_pk=signal_obj.pk,
        department_pks=department_pks
    )


@receiver(update_user_assignment, dispatch_uid='core_email_integrations_update_user_assignment')
def update_user_assignment_handler(sender, signal_obj, user_assignment, prev_user_assignment, *args, **kwargs):
    if user_assignment and prev_user_assignment:
        if user_assignment.user == prev_user_assignment.user:
            return  # do not trigger when the user_assignment field is unchanged

    tasks.send_mail_assigned_signal_user.delay(
        signal_pk=signal_obj.pk,
        user_pk=user_assignment.user.pk
    )
