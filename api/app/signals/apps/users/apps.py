# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'signals.apps.users'
    verbose_name = 'Users'

    def ready(self):
        from django.contrib.auth import get_user_model

        from change_log.logger import ChangeLogger
        get_user_model().add_to_class(
            'logger', ChangeLogger(track_fields=('first_name', 'last_name', 'is_active', 'groups'))
        )
