from datapunt_api.serializers import HALSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.api.v1.serializers.routing import RoutingExpressionSerializer
from signals.apps.signals.models import (
    Expression,
    ExpressionContext,
    ExpressionType,
    RoutingExpression
)


class ExpressionContextSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='_type.name')

    class Meta:
        model = ExpressionContext
        fields = ('identifier', 'identifier_type', 'type',)


class ExpressionSerializer(HALSerializer):
    id = serializers.ReadOnlyField()
    type = serializers.ReadOnlyField(source='_type.name')
    routing_department = RoutingExpressionSerializer(required=False)

    class Meta:
        model = Expression
        fields = ('id', 'name', 'code', 'type', 'routing_department',)

    def validate(self, data):
        try:
            exp_type = ExpressionType.objects.get(name=self.initial_data['type'])
            data['_type'] = exp_type
        except ExpressionType.DoesNotExist:
            raise ValidationError('type: {} does not exists'.format(self.initial_data['type']))
        return data

    def update(self, instance, validated_data):
        routing_data = validated_data.pop('routing_department', None)
        if routing_data:
            RoutingExpression.objects.update_routing(instance, routing_data)
            instance.refresh_from_db()

        return super(ExpressionSerializer, self).update(instance, validated_data)
