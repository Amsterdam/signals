# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.utils.timezone import now

from signals.apps.my_signals.models import Token
from signals.celery import app


@app.task
def delete_expired_tokens():
    Token.objects.filter(expires_at__lt=now()).delete()
