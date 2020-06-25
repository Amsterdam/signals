from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = 'signals.apps.search'
    verbose_name = 'Search (elastic) integration'

    def ready(self):
        from . import signal_receivers  # noqa
        from .settings import app_settings

        from elasticsearch_dsl import connections

        host = app_settings.CONNECTION['HOST'] or 'localhost'
        connections.create_connection(hosts=[host, ])
