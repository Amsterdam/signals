# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from django.apps import AppConfig


class SignalsConfig(AppConfig):
    name = 'signals.apps.signals'
    verbose_name = 'Signals'

    def ready(self):
        # Import Django signals to connect receiver functions.
        import signals.apps.signals.signal_receivers  # noqa
