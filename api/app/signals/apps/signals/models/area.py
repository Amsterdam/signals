from django.contrib.gis.db import models
from django.apps import apps
from django.db import transaction
from django.dispatch import Signal as DjangoSignal

action_create_initial = DjangoSignal(providing_args=['model', 'instance'])
action_update = DjangoSignal(providing_args=['model', 'instance', 'prev_instance'])


class AreaType(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    description = models.TextField(max_length=3000)


# We want to track the creation and edit history of an area. Since area
# instances do not comprise a lot of data, we just copy the data to a history
# table that shadows the Area table.


class HistoryManager(models.Manager):
    """Base class for ModelManagers that track history for a model"""
    TRACKED_MODEL = None  # set to correct value in sub class
    HISTORY_MODEL = None  # set to correct value in sub class

    def create_initial(self, user, **data):
        tracked_model = apps.get_model(self.TRACKED_MODEL)
        history_model = apps.get_model(self.HISTORY_MODEL)

        with transaction.atomic():
            new_instance = tracked_model.objects.create(**data)

            history_data = data.copy()
            history_data['_tracked_pk'] = new_instance.id
            history_data['_created_by'] = user
            history_entry = history_model.objects.create(**history_data)
            history_entry.save()

            transaction.on_commit(lambda: action_create_initial.send_robust(
                model=tracked_model, instance=new_instance
            ))
        return new_instance

    def update(self, user, pk, **data):
        tracked_model = apps.get_model(self.TRACKED_MODEL)
        history_model = apps.get_model(self.HISTORY_MODEL)

        with transaction.atomic():
            instance = tracked_model.objects.get(id=pk)
            prev_instance = history_model.objects.filter(_tracked_pk=pk).last()

            # Prepare new history table entry
            history_data = data.copy()  # Fails on partial update
            history_data['_tracked_pk'] = instance.id
            history_data['_created_by'] = user
            # Partial updates (copy missing values from current model instance)
            # FIXME: assumes primary key is called 'id' (Django behavior)
            for field in tracked_model._meta.fields:
                if field.name not in history_data and field.name != 'id':
                    history_data[field.name] = getattr(instance, field.name)
            history_model.objects.create(**history_data)

            # Finally update the instance.
            history_fields = set(['_tracked_pk', '_created_at', '_created_by'])
            tracked_fields = set([f.name for f in tracked_model._meta.get_fields()])

            for key, value in data.items():
                if key in history_fields or key == 'id':
                    continue
                if key in tracked_fields:
                    setattr(instance, key, value)
            instance.save()

            # And send out Django signals on commit
            transaction.on_commit(lambda: action_create_initial.send_robust(
                model=tracked_model, instance=instance, prev_instance=prev_instance
            ))
        return instance


class AreaManager(HistoryManager):
    TRACKED_MODEL = 'signals.Area'
    HISTORY_MODEL = 'signals.AreaHistory'


class AreaMutableFields(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    _type = models.ForeignKey(AreaType, on_delete=models.CASCADE)
    geometry = models.MultiPolygonField()

    class Meta:
        abstract = True


class HistoryBase(models.Model):
    _tracked_pk = models.PositiveIntegerField()

    _created_at = models.DateTimeField(auto_now_add=True)
    _created_by = models.EmailField(null=True)

    class Meta:
        abstract = True
        ordering = ['_created_at']


class AreaHistory(HistoryBase, AreaMutableFields):
    """Do not use directly, is used internally to track history of Area."""
    pass


class Area(AreaMutableFields):
    objects = models.Manager()
    actions = AreaManager()
