from django.contrib.auth import get_user_model
from rest_framework.relations import PrimaryKeyRelatedField

from signals.apps.api.generics.serializers import SIAModelSerializer

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
