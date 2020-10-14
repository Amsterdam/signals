from datapunt_api.serializers import HALSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.signals.models import Expression, ExpressionContext, ExpressionType


class ExpressionContextSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='_type.name')

    class Meta:
        model = ExpressionContext
        fields = ('identifier', 'identifier_type', 'type',)


class ExpressionSerializer(HALSerializer):
    id = serializers.ReadOnlyField()
    type = serializers.ReadOnlyField(source='_type.name')

    class Meta:
        model = Expression
        fields = ('id', 'name', 'code', 'type', )

    def validate(self, data):
        try:
            exp_type = ExpressionType.objects.get(name=self.initial_data['type'])
            data['_type'] = exp_type
        except ExpressionType.DoesNotExist:
            raise ValidationError('type: {} does not exists'.format(self.initial_data['type']))
        return data
