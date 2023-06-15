# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'signals.apps.api'
    verbose_name = 'REST API App'

    def ready(self):
        import signals.auth.schema  # noqa: F401
