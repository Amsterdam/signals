# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Delta10 B.V.
from django.conf import settings
from django.apps import AppConfig


class ZgwConfig(AppConfig):
    name = 'signals.apps.zgw'
    verbose_name = 'Replicate Signals to a case management system using the ZGW API standard'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from . import signal_receivers  # noqa
