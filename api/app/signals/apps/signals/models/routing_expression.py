from django.contrib.gis.db import models

from signals.apps.signals.models import Department, Expression


class RoutingExpression(models.Model):
    _expression = models.ForeignKey(Expression, on_delete=models.CASCADE)
    _department = models.ForeignKey(Department, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        unique_together = ('_expression', '_department')
