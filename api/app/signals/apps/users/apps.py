# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam
from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'signals.apps.users'
    verbose_name = 'Users'

    def ready(self):
        from django.contrib.auth import get_user_model
        from django.contrib.contenttypes.fields import GenericRelation

        # Adding History log to the User model
        user_model = get_user_model()
        user_model.add_to_class('track_fields', ('first_name', 'last_name', 'is_active', 'groups'))
        user_model.add_to_class('history_log', GenericRelation('history.Log', object_id_field='object_pk'))

        def from_db(cls, db, field_names, values):
            new = super(user_model, cls).from_db(db, field_names, values)
            from signals.apps.history.models.mixins import track_fields_data_from_instance
            new._state.initial_data = track_fields_data_from_instance(new, cls.track_fields)
            return new
        user_model.add_to_class('from_db', classmethod(from_db))

        def refresh_from_db(self, using=None, fields=None):
            super(user_model, self).refresh_from_db(using=using, fields=fields)
            from signals.apps.history.models.mixins import track_fields_data_from_instance
            self._state.initial_data = track_fields_data_from_instance(self, self.track_fields)
        user_model.add_to_class('refresh_from_db', refresh_from_db)

        def changed_data(self):
            from signals.apps.history.models.mixins import changed_field_data
            return changed_field_data(self)
        user_model.add_to_class('changed_data', changed_data)

        def save(self, *args, **kwargs):
            super(user_model, self).save(*args, **kwargs)

            from signals.apps.history.services import HistoryLogService
            HistoryLogService.log_update(self)
        user_model.add_to_class('save', save)
