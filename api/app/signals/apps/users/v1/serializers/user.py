from datapunt_api.rest import HALSerializer
from datapunt_api.serializers import DisplayField
from django.contrib.auth.models import Group, User
from django.core.validators import EmailValidator
from rest_framework import serializers

from change_log.models import Log
from signals.apps.api.generics.mixins import WriteOnceMixin
from signals.apps.users.v1.fields.user import UserHyperlinkedIdentityField
from signals.apps.users.v1.serializers import (
    PermissionSerializer,
    ProfileDetailSerializer,
    ProfileListSerializer,
    RoleSerializer
)


def _get_groups_queryset():
    return Group.objects.all()


class UserListHALSerializer(WriteOnceMixin, HALSerializer):
    _display = DisplayField()
    roles = serializers.SerializerMethodField()
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True, required=False, read_only=False, write_only=True,
        queryset=_get_groups_queryset(), source='groups'
    )
    profile = ProfileListSerializer(required=False)

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
    serializer_url_field = UserHyperlinkedIdentityField
    _display = DisplayField()
    roles = RoleSerializer(source='groups', many=True, read_only=True)
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True, required=False, read_only=False, write_only=True,
        queryset=_get_groups_queryset(), source='groups'
    )
    permissions = PermissionSerializer(source='user_permissions', many=True, read_only=True)
    profile = ProfileDetailSerializer(required=False)

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

        profile_data = validated_data.pop('profile', None)

        validated_data['email'] = validated_data['username']  # noqa The email address and username are basically the same. TODO refactor this behavior in the user model
        instance = super(UserDetailHALSerializer, self).create(validated_data=validated_data)

        if profile_data:
            profile_detail_serializer = ProfileDetailSerializer()
            profile_detail_serializer.update(instance=instance.profile,
                                             validated_data=profile_data)

        instance.refresh_from_db()

        return instance

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        if profile_data:
            profile_detail_serializer = ProfileDetailSerializer()
            profile_detail_serializer.update(instance=instance.profile,
                                             validated_data=profile_data)

        groups = validated_data.pop('groups', None)
        if groups or isinstance(groups, (list, tuple)):
            instance.groups.set(groups)

        instance = super(UserDetailHALSerializer, self).update(instance=instance,
                                                               validated_data=validated_data)

        return instance


class PrivateUserHistoryHalSerializer(serializers.ModelSerializer):
    identifier = serializers.SerializerMethodField()
    what = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    _user = serializers.IntegerField(source='object_id', read_only=True)

    class Meta:
        model = Log
        fields = (
            'identifier',
            'when',
            'what',
            'action',
            'description',
            'who',
            '_user',
        )

    def get_identifier(self, log):
        return f'{log.get_action_display().upper()}_USER_{log.id}'

    def get_what(self, log):
        return f'{log.get_action_display().upper()}_USER'

    def get_action(self, log):
        key_2_title = {
            'first_name': 'Voornaam gewijzigd',
            'last_name': 'Achternaam gewijzigd',
            'is_active': 'Status wijziging',
            'groups': 'Rol wijziging',
        }

        actions = []
        for key, value in log.data.items():
            if key == 'groups':
                value = ', '.join(_get_groups_queryset().filter(id__in=value).values_list('name', flat=True))
            elif key == 'is_active':
                value = 'Actief' if value else 'Inactief'

            actions.append(f'{key_2_title[key]}:\n {value if value else "-"}')
        return f'\n'.join(actions)

    def get_description(self, log):
        return None
