from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = 'signals.apps.search'
    verbose_name = 'Search (elastic) integration'

    def ready(self):
        from . import signal_receivers  # noqa
        from .settings import search_settings

        from elasticsearch_dsl import connections

        for alias, alias_settings in search_settings.ELASTIC['connections'].items():
            connections.create_connection(alias=alias, **alias_settings)
