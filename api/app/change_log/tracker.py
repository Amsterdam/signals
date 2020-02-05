from copy import deepcopy


class BaseChangeTracker:
    def __init__(self, instance):
        self.instance = instance  # This contains the instance we are tracking
        self.data = {}

    def store_state(self):
        for field in self.instance._meta.fields:
            self.data[field.name] = deepcopy(getattr(self.instance, field.name))

    @property
    def instance_changed(self):
        for field in self.instance._meta.fields:
            if getattr(self.instance, field.name) != self.data.get(field.name):
                return True
        return False

    def changed_data(self):
        changed = {}
        for field in self.instance._meta.fields:
            new_value = getattr(self.instance, field.name)
            prev_value = self.data.get(field.name)
            if new_value != prev_value:
                changed[field.name] = new_value
        return changed


class ChangeTracker(BaseChangeTracker):
    pass
