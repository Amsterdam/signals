from datapunt_api.rest import HALSerializer
from datapunt_api.serializers import DisplayField
from django.contrib.auth.models import User
from rest_framework import serializers

from signals.apps.users.v1.serializers.permissions import PermissionSerializer
from signals.apps.users.v1.serializers.roles import RoleSerializer


class UserListHALSerializer(HALSerializer):
    _display = DisplayField()
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            '_links',
            '_display',
            'id',
            'username',
            'is_active',
            'roles',
        )

    def get_roles(self, obj):
        return [group.name for group in obj.groups.all()]


class UserDetailHALSerializer(HALSerializer):
    _display = DisplayField()
    roles = RoleSerializer(source='groups', many=True)
    permissions = PermissionSerializer(source='user_permissions', many=True)

    class Meta:
        model = User
        fields = (
            '_links',
            '_display',
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'is_staff',
            'is_superuser',
            'roles',
            'permissions',
        )
