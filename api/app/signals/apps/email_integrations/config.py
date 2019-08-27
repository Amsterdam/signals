from django.apps import AppConfig


class EmailIntegrationsConfig(AppConfig):
    name = 'signals.apps.email_integrations'
    verbose_name = 'E-mail integrations'

    def ready(self):
        # Load the app settings
        from .settings import app_settings  # noqa

        # The core signal receivers
        import signals.apps.email_integrations.reporter.signal_receivers  # noqa

        # The signal receivers for external mail integrations
        import signals.apps.email_integrations.flex_horeca.signal_receivers  # noqa
        import signals.apps.email_integrations.toezicht_or_nieuw_west.signal_receivers  # noqa
        import signals.apps.email_integrations.vth_nieuw_west.signal_receivers  # noqa
