# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
import logging

from django.contrib.auth import get_user_model

from signals.apps.email_integrations.services import MailService
from signals.apps.signals.models import Department, Signal
from signals.celery import app

logger = logging.getLogger(__name__)
User = get_user_model()


@app.task
def send_mail_reporter(pk):
    MailService.status_mail(signal=pk)


@app.task
def send_mail_assigned_signal_departments(signal_pk, department_pks):
    try:
        signal = Signal.objects.get(pk=signal_pk)
    except Signal.DoesNotExist:
        logger.exception()
        return

    for department_pk in department_pks:
        try:
            department = Department.objects.get(pk=department_pk)
        except Department.DoesNotExist:
            logger.exception()
            continue

        user_profiles = department.user_profiles.select_related('user').filter(
            user__is_active=True,
            notification_on_department_assignment=True
        )

        for profile in user_profiles:
            MailService.system_mail(signal=signal,
                                    action_name='assigned',
                                    recipient=profile.user,
                                    assigned_to=department)


@app.task
def send_mail_assigned_signal_user(signal_pk, user_pk):
    try:
        signal = Signal.objects.get(pk=signal_pk)
    except Signal.DoesNotExist:
        logger.exception()
        return

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.exception()
        return

    if not user.is_active:
        return

    if not user.profile.notification_on_user_assignment:
        return

    MailService.system_mail(signal=signal,
                            action_name='assigned',
                            recipient=user,
                            assigned_to=user)
