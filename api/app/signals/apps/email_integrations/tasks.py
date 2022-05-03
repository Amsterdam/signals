# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from signals.apps.email_integrations.services import MailService
from signals.celery import app


@app.task
def send_mail_reporter(pk):
    MailService.status_mail(signal=pk)


@app.task
def send_system_mail(signal_id: str, action_name: str, **kwargs):
    """
    Task to send a specific mail based for a signal
    """
    MailService.system_mail(signal_id, action_name, **kwargs)
