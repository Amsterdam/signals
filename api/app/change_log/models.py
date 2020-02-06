from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django_extensions.db.fields.json import JSONField


class Log(models.Model):
    # The object that has his changes logged
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    object_id = models.PositiveIntegerField(db_index=True)
    object = GenericForeignKey('content_type', 'object_id')

    # The action that has been performed on the model, when and by who (not a foreignkey)
    action = models.CharField(max_length=1, choices=(
        ('I', 'Inserted'),
        ('U', 'Updated')
    ))
    when = models.DateTimeField(auto_now_add=True)
    who = models.EmailField(null=True)

    # The data that has been changed
    data = JSONField(null=True)

    class Meta:
        ordering = ['content_type', 'object_id', '-when']
        index_together = [
            ['content_type', 'object_id'],
        ]
        db_table = 'change_log'  # Just a nicer name than 'change_log_log'

    def update(self, *args, **kwargs):
        # We never update anything in the change log
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        # We never delete anything from the change log
        raise NotImplementedError
