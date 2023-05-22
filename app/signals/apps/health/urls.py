# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam
from django.urls import path

from signals.apps.health.views import health

urlpatterns = [
    path('health', health, name='health_check'),
]
