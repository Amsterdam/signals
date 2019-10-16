from datapunt_api.rest import HALSerializer
from datapunt_api.serializers import DisplayField
from django.contrib.auth.models import Group, Permission, User
from django.core.validators import EmailValidator
from rest_framework import serializers

from signals.apps.api.generics.mixins import WriteOnceMixin
from signals.apps.users.models import Profile
from signals.apps.users.v1.serializers.permissions import PermissionSerializer
from signals.apps.users.v1.serializers.profiles import ProfileDetailSerializer, ProfileSerializer
from signals.apps.users.v1.serializers.roles import RoleSerializer


def _get_groups_queryset():
    return Group.objects.all()


def _get_permissions_queryset():
    return Permission.objects.all()


class UserListHALSerializer(WriteOnceMixin, HALSerializer):
    _display = DisplayField()
    roles = serializers.SerializerMethodField()
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True, required=False, read_only=False, write_only=True,
        queryset=_get_groups_queryset(), source='groups'
    )
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            '_links',
            '_display',
            'id',
            'username',
            'is_active',
            'roles',
            'role_ids',
            'profile',
        )
        extra_kwargs = {
            'email': {'read_only': True},
            'username': {'validators': [EmailValidator()]},
        }
        write_once_fields = (
            'username',
        )

    def get_roles(self, obj):
        return [group.name for group in obj.groups.all()]


class UserDetailHALSerializer(WriteOnceMixin, HALSerializer):
    _display = DisplayField()
    roles = RoleSerializer(source='groups', many=True, read_only=True)
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True, required=False, read_only=False, write_only=True,
        queryset=_get_groups_queryset(), source='groups'
    )
    permissions = PermissionSerializer(source='user_permissions', many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True, required=False, read_only=False, write_only=True,
        queryset=_get_permissions_queryset(), source='user_permissions'
    )
    profile = ProfileDetailSerializer(read_only=True)

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
            'role_ids',
            'permissions',
            'permission_ids',
            'profile',
        )
        extra_kwargs = {
            'email': {'read_only': True},
            'is_staff': {'read_only': True},
            'is_superuser': {'read_only': True},
            'username': {'validators': [EmailValidator()]},
        }
        write_once_fields = (
            'username',
        )

    def create(self, validated_data):
        self.get_extra_kwargs()
        validated_data['email'] = validated_data['username']  # noqa The email address and username are basically the same. TODO refactor this behaviour in the user model
        instance = super(UserDetailHALSerializer, self).create(validated_data=validated_data)

        # TODO: Refactor this when implementing the profile. This is a basic base implementation
        Profile.objects.create(user=instance)
        instance.refresh_from_db()

        return instance
