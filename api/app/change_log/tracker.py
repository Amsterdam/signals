from copy import deepcopy
from django.contrib.gis.db import models


class BaseChangeTracker:
    """
    !!! Bulk operations are not supported by this implementation !!!

    TODO: Fix ManyToManyRel and ManyToOneRel to be logged,
          for now we have a workaround. In the serializers of the signal project we add the many to many relations
          and also call the save/update methods. This way the ChangeLogger will be able to activate the tracker. The
          tracker needs to store and check the relations on init and save to see if it has changed or not.
    """
    _track_fields = '__all__'  # By default track all fields

    def __init__(self, instance, track_fields='__all__'):
        self.instance = instance  # This contains the instance we are tracking
        self._track_fields = track_fields
        self.data = {}

    def _track_field(self, field):
        return self._track_fields == '__all__' or self._get_field_name(field=field) in self._track_fields

    def _skip_field(self, field):
        return not self._track_field(field=field)

    def _get_field_name(self, field):
        if isinstance(field, (models.ManyToManyRel, models.ManyToOneRel)):
            return field.get_accessor_name()
        return field.name

    def _get_current_value(self, field):
        field_name = self._get_field_name(field=field)
        if isinstance(field, (models.OneToOneRel)):
            field_name = field.get_accessor_name()
            try:
                self.data[field_name] = getattr(self.instance, field_name).pk
            except Exception:
                self.data[field_name] = None
        elif isinstance(field, (models.ManyToManyRel, models.ManyToOneRel, models.ManyToManyField)):
            if self.instance.pk:
                return list(getattr(self.instance, field_name).values_list('pk', flat=True))
            return None
        return getattr(self.instance, field_name)

    def _get_previous_value(self, field):
        return self.data.get(self._get_field_name(field=field))

    def store_state(self):
        """
        Stores the current state of an instance. Is called in the ChangeLogger when initializing the logger.
        """
        for field in self.instance._meta.get_fields():
            if self._track_field(field=field):
                field_name = self._get_field_name(field=field)
                self.data[field_name] = deepcopy(self._get_current_value(field=field))

    @property
    def instance_changed(self):
        return bool(self.changed_data())

    def changed_data(self):
        """
        Returns the diff of the state stored on init and the state after saving
        """
        _changed_data = {}
        for field in self.instance._meta.get_fields():
            if self._skip_field(field=field):
                continue

            current_value = self._get_current_value(field=field)
            previous_value = self._get_previous_value(field=field)

            if current_value == previous_value:
                continue

            field_name = self._get_field_name(field=field)
            if isinstance(field, (models.ManyToManyRel, models.ManyToOneRel)):
                changes = set(current_value or []) - set(previous_value or [])
                if changes:
                    _changed_data[field_name] = list(changes)
            else:
                _changed_data[field_name] = current_value

        return _changed_data


class ChangeTracker(BaseChangeTracker):
    """
    Used as the default tracker class, will try to log all fields of a model declared in the self._track_fields.
    Including ManyToMany and ManyToOne relations.

    If you need custom tracking just create a new tracker based on the BaseChangeTracker class
    """
    pass
