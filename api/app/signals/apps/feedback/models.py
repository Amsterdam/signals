import datetime
import uuid

from django.contrib.gis.db import models

from signals.apps.signals.models import CreatedUpdatedModel, Signal

FEEDBACK_EXPECTED_WITHIN_N_DAYS = 14  # move to general settings file


class StandardAnswer(models.Model):
    is_visible = models.BooleanField(default=True)
    is_satisfied = models.BooleanField(default=True)
    text = models.TextField(max_length=1000)


class Feedback(CreatedUpdatedModel):
    uuid = models.UUIDField(db_index=True, primary_key=True, default=uuid.uuid4)

    _signal = models.ForeignKey(Signal, on_delete=models.CASCADE, related_name='feedback')
    requested_before = models.DateTimeField(editable=False)  # should be something like now + 14 days ...
    is_satisfied = models.BooleanField(null=True)
    allows_contact = models.BooleanField(default=False)
    text = models.TextField(max_length=1000, null=True, blank=True)
