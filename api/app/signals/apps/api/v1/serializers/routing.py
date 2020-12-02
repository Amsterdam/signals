from rest_framework import serializers

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.v1.serializers.nested import _NestedDepartmentModelSerializer
from signals.apps.signals.models import RoutingExpression


class RoutingExpressionSerializer(serializers.ModelSerializer):
    department = _NestedDepartmentModelSerializer(
        source='_department',
        many=False,
        required=False,
        permission_classes=(SIAPermissions,),
    )

    class Meta:
        model = RoutingExpression
        fields = ('department', 'order',)
