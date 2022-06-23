# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'signals.settings')
app = Celery('signals')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
