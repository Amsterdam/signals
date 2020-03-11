from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'signals.apps.users'
    verbose_name = 'Users'

    def ready(self):
        from change_log.logger import ChangeLogger

        from django.contrib.auth import get_user_model
        get_user_model().add_to_class(
            'logger', ChangeLogger(track_fields=('first_name', 'last_name', 'is_active', 'groups'))
        )
