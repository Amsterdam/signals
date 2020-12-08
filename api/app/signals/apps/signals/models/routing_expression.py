from django.contrib.gis.db import models

from signals.apps.signals.models import Department, Expression


class RoutingExpression(models.Model):
    # we only allow one department routing per expression
    _expression = models.OneToOneField(
        Expression,
        on_delete=models.CASCADE,
        unique=True,
        related_name='routing_department'
    )
    _department = models.ForeignKey(Department, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=False)

    objects = models.Manager()
