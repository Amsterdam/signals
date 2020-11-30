from django.contrib.gis.db import models

from signals.apps.signals.models import Department, Expression


class RoutingExpressionManager(models.Manager):
    def update_routing(self, instance, data):
        department = data['_department']['id']
        order = data.get('order', None)
        if not hasattr(instance, 'routing_department'):
            instance.routing_department = RoutingExpression.objects.create(
                _department=department,
                _expression=instance,
                order=order
            )
        else:
            instance.routing_department._department = department
            instance.routing_department.order = order
            instance.routing_department.save()


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

    actions = RoutingExpressionManager()
    objects = models.Manager()
