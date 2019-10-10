from datapunt_api.rest import HALSerializer
from datapunt_api.serializers import DisplayField
from django.contrib.auth.models import Group

from signals.apps.users.v1.serializers.permissions import PermissionSerializer


class RoleSerializer(HALSerializer):
    _display = DisplayField()
    permissions = PermissionSerializer(many=True)

    class Meta:
        model = Group
        fields = (
            '_links',
            '_display',
            'id',
            'name',
            'permissions',
        )
