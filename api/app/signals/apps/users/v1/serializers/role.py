from datapunt_api.rest import HALSerializer
from datapunt_api.serializers import DisplayField
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from rest_framework import serializers

from signals.apps.users.v1.serializers import PermissionSerializer


def _get_permissions_queryset():
    return Permission.objects.filter(Q(codename__istartswith='sia_') | Q(codename='push_to_sigmax'))


class RoleSerializer(HALSerializer):
    _display = DisplayField()
    permissions = PermissionSerializer(many=True, required=False, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True, required=False, read_only=False, write_only=True,
        queryset=_get_permissions_queryset(), source='permissions'
    )

    class Meta:
        model = Group
        fields = (
            '_links',
            '_display',
            'id',
            'name',
            'permissions',
            'permission_ids',
        )
