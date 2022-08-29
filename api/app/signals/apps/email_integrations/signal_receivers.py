# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
from django.dispatch import receiver

from signals.apps.email_integrations.services import MailService
from signals.apps.email_integrations import tasks
from signals.apps.signals.managers import create_initial, update_status, update_user_assignment, update_signal_departments
from email.utils import formataddr


@receiver((create_initial, update_status), dispatch_uid='core_email_integrations_update_status')
def update_status_handler(sender, signal_obj, *args, **kwargs):
    tasks.send_mail_reporter.delay(pk=signal_obj.pk)

@receiver(update_signal_departments, dispatch_uid='core_email_integrations_update_signal_departments')
def update_signal_departments_handler(sender, signal_obj, signal_departments, prev_signal_departments, *args, **kwargs):
    # TODO: uncomment
    #if signal_departments and prev_signal_departments and set(signal_departments.departments.all()) == set(prev_signal_departments.departments.all()):
    #    return

    # TODO: make async
    for department in signal_departments.departments.all():
        for profile in department.profiles.filter(notification_on_assigment_to_department=True):
            MailService.system_mail(signal=signal_obj,
                                    action_name='assigned',
                                    recipient_list=[
                                        formataddr((profile.user.get_full_name(), profile.user.email))
                                    ]
            )

@receiver(update_user_assignment, dispatch_uid='core_email_integrations_update_user_assignment')
def update_user_assignment(sender, signal_obj, user_assignment, prev_user_assignment, *args, **kwargs):
    if user_assignment and prev_user_assignment and user_assignment.user == prev_user_assignment.user:
        return

    if not user_assignment.user.profile.notification_on_assigment_to_user:
        return

    # TODO: make async
    MailService.system_mail(signal=signal_obj,
                            action_name='assigned',
                            recipient_list=[
                                formataddr((user_assignment.user.get_full_name(), user_assignment.user.email))
                            ]
    )
