# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib.gis.db import models
from django.core.exceptions import FieldDoesNotExist


def track_fields_data_from_instance(instance, track_fields=None):
    initial_data = {}
    for field_name in track_fields or []:
        try:
            field = instance._meta.get_field(field_name=field_name)
        except FieldDoesNotExist:
            continue

        field_value = getattr(instance, field_name)
        if isinstance(field, (models.ManyToManyRel, models.ManyToOneRel, models.ManyToManyField)):
            field_value = list(field_value.values_list('pk', flat=True))
        elif isinstance(field, models.OneToOneRel):
            field_value = [field_value.pk]

        initial_data.update({field_name: field_value})
    return initial_data


class TrackFields:
    """
    Mixin stores initial data from the db when creating a model instance. Updates the datat when refresh_from_db
    has been called. Also adds a function that returns the changed data. All data stored and checked are based on the
    set track_fields.
    """
    track_fields = []

    @classmethod
    def from_db(cls, db, field_names, values):
        new = super(TrackFields, cls).from_db(db, field_names, values)
        new._state.initial_data = track_fields_data_from_instance(new, cls.track_fields)
        return new

    def refresh_from_db(self, using=None, fields=None):
        super().refresh_from_db(using=using, fields=fields)
        self._state.initial_data = track_fields_data_from_instance(self, self.track_fields)

    def changed_data(self):
        if not hasattr(self._state, 'initial_data'):
            return {}  # Could not determine changed data

        current_data = track_fields_data_from_instance(self, self.track_fields)

        changed_data = {}
        for field_name in self.track_fields:
            initial_value = self._state.initial_data[field_name]
            current_value = current_data[field_name]

            if initial_value != current_value:
                if isinstance(current_value, list):
                    # Only store the difference
                    current_value = list(set(current_value) - set(initial_value))
                changed_data.update({field_name: current_value})
        return changed_data
