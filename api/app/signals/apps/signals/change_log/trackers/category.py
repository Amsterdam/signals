from django.contrib.gis.db import models
from django_extensions.db.fields import AutoSlugField

from change_log.tracker import BaseChangeTracker


class CategoryChangeTracker(BaseChangeTracker):
    # Skip these fields
    _skip_fields = ['id', 'slug', 'parent', 'children', 'category_assignments', 'signal_set',
                    'status_message_templates', 'translations', 'handling', 'categorydepartment_set']

    def _skip_field(self, field):
        return self._get_field_name(field=field) in self._skip_fields

    def _get_field_name(self, field):
        if isinstance(field, (models.ManyToManyRel, models.ManyToOneRel)):
            return field.get_accessor_name()
        return field.name

    def _get_current_value(self, field):
        field_name = self._get_field_name(field=field)
        if isinstance(field, (models.ManyToManyRel, models.ManyToOneRel)):
            return list(getattr(self.instance, field_name).values_list('pk', flat=True))
        return getattr(self.instance, field_name)

    def _get_previous_value(self, field):
        return self.data[self._get_field_name(field=field)]

    def changed_data(self):
        """
        Override the default ChangeTracker.

        This custom ChangeTracker for Categories is used to make sure the changes are stored correctly in the JSON
        field (data) of the change_log.
        """
        _changed_data = dict()  # Here we are going to keep track of the changes

        for field in self.instance._meta.get_fields():
            if self._skip_field(field=field):
                # skip these fields for now, we do not track them because these cannot be changed
                continue

            # The name of the field
            field_name = self._get_field_name(field=field)

            # The value of the field that is currently saved to the database
            current_value = self._get_current_value(field=field)

            # Contains the value the field had when the instance was initialized
            previous_value = self._get_previous_value(field=field)

            # Duh! Let's check if the values are different
            if current_value != previous_value:
                if field_name == 'slo':
                    # Only track the latest added sla, no bulk change is available at this moment
                    # We only add items and do not remove them from the list
                    changed_value = set(current_value) - set(previous_value)
                    _changed_data[field_name] = changed_value.pop()
                elif isinstance(field, (AutoSlugField, models.CharField, models.TextField, models.BooleanField)):
                    # Let's just use the json representation of these fields
                    _changed_data[field_name] = current_value

        return _changed_data
