from django.apps import AppConfig


class ZDSConfig(AppConfig):
    name = 'signals.apps.zds'
    verbose_name = 'ZDS'

    def ready(self):
        # Import Django signals to connect receiver functions.
        import signals.apps.zds.signal_receivers  # noqa
