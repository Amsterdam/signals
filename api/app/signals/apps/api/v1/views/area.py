from datapunt_api.rest import DatapuntViewSet
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend

from signals.apps.api.generics.pagination import LinkHeaderPagination
from signals.apps.api.v1.filters import AreaFilterSet
from signals.apps.api.v1.serializers.area import AreaGeoSerializer
from signals.apps.signals.models import Area
from signals.auth.backend import JWTAuthBackend


class PublicAreasViewSet(DatapuntViewSet):
    """
    V1 Public ViewSet to display all area's in the database
    """
    queryset = Area.objects.all()
    queryset_detail = Area.objects.all()

    serializer_class = AreaGeoSerializer
    serializer_detail_class = AreaGeoSerializer

    pagination_class = LinkHeaderPagination

    authentication_classes = ()

    filter_backends = (DjangoFilterBackend, )
    filterset_class = AreaFilterSet

    def retrieve(self, request, *args, **kwargs):
        raise Http404


class PrivateAreasViewSet(PublicAreasViewSet):
    """
    V1 Private ViewSet to display all area's in the database
    """
    authentication_classes = (JWTAuthBackend, )
