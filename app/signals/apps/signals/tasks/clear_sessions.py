# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.core.management import call_command

from signals.celery import app


@app.task
def clearsessions():
    """
    This task makes it possible to configure the "clearsession" management command through Celery
    """
    call_command('clearsessions')
