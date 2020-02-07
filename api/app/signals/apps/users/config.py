from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'signals.apps.users'
    verbose_name = 'Users'

    def ready(self):
        from change_log.logger import ChangeLogger
        from signals.apps.users.change_log.tracker.user import UserChangeTracker

        from django.contrib.auth import get_user_model
        get_user_model().add_to_class('logger', ChangeLogger(tracker_class=UserChangeTracker))
