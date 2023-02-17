# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = 'signals.apps.search'
    verbose_name = 'Search (elastic) integration'

    def ready(self):
        from . import signal_receivers  # noqa
        from elasticsearch_dsl import connections

        from .settings import app_settings

        host = app_settings.CONNECTION['HOST'] or 'localhost'
        connections.create_connection(hosts=[host, ])
