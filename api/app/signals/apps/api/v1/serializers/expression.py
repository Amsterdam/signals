from datapunt_api.serializers import HALSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.signals.models import Expression, ExpressionContext, ExpressionType


class ExpressionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpressionType
        fields = ('name', )


class ExpressionContextSerializer(serializers.ModelSerializer):
    type = ExpressionTypeSerializer(source='_type')

    class Meta:
        model = ExpressionContext
        fields = ('identifier', 'identifier_type', 'type',)


class ExpressionSerializer(HALSerializer):
    type = ExpressionTypeSerializer(source='_type')

    class Meta:
        model = Expression
        fields = ('id', 'name', 'code', 'type', )


class ExpressionModificationSerializer(serializers.ModelSerializer):
    type = serializers.PrimaryKeyRelatedField(read_only=True, source='_type')

    class Meta(object):
        model = Expression
        fields = (
            'name',
            'code',
            'type',
        )

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
