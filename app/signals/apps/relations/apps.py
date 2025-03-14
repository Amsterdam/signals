from django.apps import AppConfig


class RelationsConfig(AppConfig):
    name = 'signals.apps.relations'
    verbose_name = 'Relations between signals'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from . import signal_receivers  # noqa
