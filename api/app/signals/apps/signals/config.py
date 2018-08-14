from django.apps import AppConfig


class SignalsConfig(AppConfig):
    name = 'signals.apps.signals'
    verbose_name = 'Signals'

    def ready(self):
        # Import Django signals to connect receiver functions.
        import signals.django_signals  # noqa
