from django.apps import AppConfig


class SigmaxConfig(AppConfig):
    name = 'signals.apps.sigmax'
    verbose_name = 'Sigmax'

    def ready(self):
        # Import Django signals to connect receiver functions.
        import signals.apps.sigmax.signal_receivers  # noqa
