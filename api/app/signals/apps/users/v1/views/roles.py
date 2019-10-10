from datapunt_api.rest import DatapuntViewSet
from django.contrib.auth.models import Group

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.users.v1.serializers.roles import RoleSerializer
from signals.auth.backend import JWTAuthBackend


class RoleViewSet(DatapuntViewSet):
    queryset = Group.objects.prefetch_related(
        'permissions',
    ).all()

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    serializer_detail_class = RoleSerializer
    serializer_class = RoleSerializer
