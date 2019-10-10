from datapunt_api.rest import DatapuntViewSet
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.users.v1.filters import UserFilter
from signals.apps.users.v1.serializers.users import UserDetailHALSerializer, UserListHALSerializer
from signals.auth.backend import JWTAuthBackend


class UserViewSet(DatapuntViewSet):
    queryset = User.objects.prefetch_related(
        'groups',
        'groups__permissions',
    ).all()

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    serializer_detail_class = UserDetailHALSerializer
    serializer_class = UserListHALSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = UserFilter
