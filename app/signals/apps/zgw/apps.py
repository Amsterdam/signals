# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Delta10 B.V.
from django.apps import AppConfig


class ZgwConfig(AppConfig):
    name = 'signals.apps.zgw'
    verbose_name = 'Replication to case management system'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from . import signal_receivers  # noqa
