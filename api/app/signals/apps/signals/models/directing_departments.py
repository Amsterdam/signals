from django.contrib.gis.db import models

from signals.apps.signals.models.mixins import CreatedUpdatedModel


class DirectingDepartments(CreatedUpdatedModel):
    _signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, related_name='directing_departments')
    departments = models.ManyToManyField('signals.Department', related_name='+')
    created_by = models.EmailField(null=True, blank=True)
