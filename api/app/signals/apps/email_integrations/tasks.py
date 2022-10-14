# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from signals.apps.email_integrations.services import MailService
from signals.celery import app


@app.task
def send_mail_reporter(pk):
    # Can also mail can also be forwarded to external party ps-261
    MailService.status_mail(signal=pk)
