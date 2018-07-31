from django.apps import AppConfig


class SignalsConfig(AppConfig):
    name = 'signals'
    verbose_name = 'Signals'

    def ready(self):
        import signals.django_signals  # noqa
