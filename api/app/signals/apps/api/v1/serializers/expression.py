from datapunt_api.serializers import HALSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.signals.models import Expression, ExpressionContext, ExpressionType


class ExpressionContextSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField('get_type_name')

    class Meta:
        model = ExpressionContext
        fields = ('identifier', 'identifier_type', 'type',)

    def get_type_name(self, obj):
        return obj._type.name


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

    def create(self, validated_data):
        try:
            return Expression.objects.create(**validated_data)
        except Exception:
            raise ValidationError('failed to create')

    def update(self, instance, validated_data):
        try:
            obj = Expression(pk=instance.pk, **validated_data)
            obj.save()
            return obj
        except Exception:
            raise ValidationError('failed to update')
