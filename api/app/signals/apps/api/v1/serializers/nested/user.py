from django.contrib.auth import get_user_model
from rest_framework.relations import PrimaryKeyRelatedField

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.generics.serializers import SIAModelSerializer
from signals.apps.users.models import SignalUser

User = get_user_model()


def _get_user_queryset():
    return User.objects.all()


class _NestedUserModelSerializer(SIAModelSerializer):
    id = PrimaryKeyRelatedField(required=False, queryset=_get_user_queryset())

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
        )
        read_only_fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
        )


class _NestedSignalUsersModelSerializer(SIAModelSerializer):
    user = _NestedUserModelSerializer(
        many=False,
        required=False,
        permission_classes=(SIAPermissions,),
    )

    class Meta:
        model = SignalUser
        fields = (
            'created_by',
            'user',
        )
