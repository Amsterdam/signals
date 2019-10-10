from datapunt_api.rest import DatapuntViewSet
from django.contrib.auth.models import Permission

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.users.v1.serializers.permissions import PermissionSerializer
from signals.auth.backend import JWTAuthBackend


class PermissionViewSet(DatapuntViewSet):
    queryset = Permission.objects.all()

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    serializer_detail_class = PermissionSerializer
    serializer_class = PermissionSerializer
