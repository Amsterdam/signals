from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'signals.apps.notifications'
    verbose_name = 'Notifications'

    def ready(self):
        from . import signal_receivers  # noqa