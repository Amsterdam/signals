from django.contrib.gis.db import models

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class SignalDepartments(CreatedUpdatedModel):
    REL_DIRECTING = 'directing'
    REL_ROUTING = 'routing'
    REL_CHOICES = (
        (REL_DIRECTING, REL_DIRECTING),
        (REL_ROUTING, REL_ROUTING),
    )

    _signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, related_name='signal_departments')
    departments = models.ManyToManyField('signals.Department', related_name='+')
    relation_type = models.CharField(max_length=20, choices=REL_CHOICES, default=REL_DIRECTING)
    created_by = models.EmailField(null=True, blank=True)
