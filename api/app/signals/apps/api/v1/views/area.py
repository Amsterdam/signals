from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from signals.apps.api.generics.pagination import LinkHeaderPagination
from signals.apps.api.v1.filters import AreaFilterSet
from signals.apps.api.v1.serializers.area import AreaGeoSerializer, AreaSerializer
from signals.apps.signals.models import Area
from signals.auth.backend import JWTAuthBackend


class PublicAreasViewSet(DatapuntViewSet):
    """
    V1 Public ViewSet to display all area's in the database
    """
    queryset = Area.objects.all()
    queryset_detail = Area.objects.all()

    serializer_class = AreaSerializer
    serializer_detail_class = AreaSerializer

    pagination_class = HALPagination

    authentication_classes = ()

    filter_backends = (DjangoFilterBackend, )
    filterset_class = AreaFilterSet

    def retrieve(self, request, *args, **kwargs):
        raise Http404

    @action(detail=False, url_path='geography/')
    def geography(self, request):
        filtered_qs = self.filter_queryset(self.get_queryset())

        paginator = LinkHeaderPagination(page_query_param='geopage')
        page = paginator.paginate_queryset(filtered_qs, self.request, view=self)
        if page is not None:
            serializer = AreaGeoSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AreaGeoSerializer(filtered_qs, many=True)
        return Response(serializer.data)


class PrivateAreasViewSet(PublicAreasViewSet):
    """
    V1 Private ViewSet to display all area's in the database
    """
    authentication_classes = (JWTAuthBackend, )
