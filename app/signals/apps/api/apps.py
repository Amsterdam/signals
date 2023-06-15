# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'signals.apps.api'
    verbose_name = 'REST API App'

    def ready(self):
        """
        This method is called after the app registry is fully populated and all
        app configs are ready. It's safe to perform initialization tasks such as
        registering signals.

        See: https://docs.djangoproject.com/en/3.2/ref/applications/#django.apps.AppConfig.ready

        In this case it is used to import the signals.auth.schema module. Which
        is needed to register the auth drf-spectacular schema.
        """
        import signals.auth.schema  # noqa: F401
