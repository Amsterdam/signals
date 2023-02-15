# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from django.apps import AppConfig


class EmailIntegrationsConfig(AppConfig):
    name = 'signals.apps.email_integrations'
    verbose_name = 'E-mail integrations'

    def ready(self):
        # The signal receivers
        import signals.apps.email_integrations.signal_receivers  # noqa
