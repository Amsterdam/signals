from datapunt_api.pagination import HALPagination
from rest_framework import mixins, viewsets

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.reporting.models import HorecaCSVExport
from signals.apps.reporting.serializers import HorecaCSVExportSerializer
from signals.auth.backend import JWTAuthBackend


class HorecaCSVExportViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    # Serializer
    serializer_class = HorecaCSVExportSerializer
    pagination_class = HALPagination
    queryset = HorecaCSVExport.objects.all()
    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)  # TODO: add SIA export or reports permission

    # No self-links
