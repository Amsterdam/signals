# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from signals.apps.email_integrations.services import MailService
from signals.celery import app


@app.task
def send_mail_reporter(pk):
    MailService.mail(signal=pk)
