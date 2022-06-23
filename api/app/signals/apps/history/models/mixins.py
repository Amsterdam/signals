# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib.gis.db import models
from django.core.exceptions import FieldDoesNotExist


def track_fields_data_from_instance(instance, track_fields=None):
    """
    This function is used to create a dict containing the data of the fields that are tracked.

    This is used to store the initial data for an instance and to compare the initial data with the current data of
    the tracked fields in the function changed_field_data
    """
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


def changed_field_data(instance):
    """
    This function is used to determine the changed data comparing the initial_data with the current_data
    """
    if not hasattr(instance._state, 'initial_data'):
        return {}  # Could not determine changed data

    current_data = track_fields_data_from_instance(instance, instance.track_fields)

    changed_data = {}
    for field_name in instance.track_fields:
        initial_value = instance._state.initial_data[field_name]
        current_value = current_data[field_name]

        if initial_value != current_value:
            if isinstance(current_value, list):
                # Only store the difference
                current_value = list(set(current_value) - set(initial_value))
            changed_data.update({field_name: current_value})
    return changed_data


class TrackFields:
    """
    Mixin stores initial data from the db when creating a model instance. Updates the data when refresh_from_db
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
        return changed_field_data(self)
