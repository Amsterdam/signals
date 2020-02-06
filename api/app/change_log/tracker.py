from copy import deepcopy
from django.contrib.gis.db import models


class BaseChangeTracker:
    """
    !!! Bulk operations are not supported by this implementation !!!

    TODO: Fix ManyToManyRel and ManyToOneRel to be logged,
          for now we have a workaround. In the serializers of the signal project we add the many to many relations
          and also call the save method. This way the ChangeLogger will be able to activate the tracker. The tracker
          needs to store and check the relations on init and save to see if it has changed or not.
    """

    def __init__(self, instance):
        self.instance = instance  # This contains the instance we are tracking
        self.data = {}

    def _many_to_many_changed(self, field_name):
        """
        Helper function that checks if ManyToMany/One relation has changed
        """
        new_values = getattr(self.instance, field_name).values_list('pk', flat=True)
        old_values = self.data.get(field_name)
        return bool(set(new_values) - set(old_values))

    def store_state(self):
        """
        Stores the current state of an instance. Is called in the ChangeLogger when initializing the logger.
        """
        for field in self.instance._meta.get_fields():
            if isinstance(field, (models.ManyToManyRel, models.ManyToOneRel)):
                field_name = field.get_accessor_name()
                if getattr(self.instance, 'id'):
                    self.data[field_name] = list(getattr(self.instance, field_name).values_list('pk', flat=True))
            elif isinstance(field, (models.ManyToManyField)):
                if getattr(self.instance, 'id'):
                    self.data[field.name] = list(getattr(self.instance, field.name).values_list('pk', flat=True))
            else:
                self.data[field.name] = deepcopy(getattr(self.instance, field.name))

    @property
    def instance_changed(self):
        return bool(self.changed_data())

    def changed_data(self):
        """
        Returns the diff of the state stored on init and the state after saving
        """
        changed = {}
        for field in self.instance._meta.get_fields():
            if isinstance(field, (models.ManyToManyRel, models.ManyToOneRel)):
                field_name = field.get_accessor_name()
                if self._many_to_many_changed(field_name):
                    changed[field_name] = list(getattr(self.instance, field_name).values_list('pk', flat=True))
            else:
                new_value = getattr(self.instance, field.name)
                prev_value = self.data.get(field.name)
                if new_value != prev_value:
                    changed[field.name] = new_value
        return changed


class ChangeTracker(BaseChangeTracker):
    """
    Used as the default tracker class, will try to log all fields of a model.
    Including ManyToMany and ManyToOne relations.

    If you need custom tracking just create a new tracker based on the BaseChangeTracker class
    """
    pass
