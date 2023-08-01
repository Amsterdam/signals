# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Gemeente Amsterdam
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from signals.apps.api.filters import AreaFilterSet
from signals.apps.api.generics.pagination import LinkHeaderPagination
from signals.apps.api.serializers.area import AreaGeoSerializer, AreaSerializer
from signals.apps.signals.models import Area
from signals.auth.backend import JWTAuthBackend


class PublicAreasViewSet(ListModelMixin, GenericViewSet):
    """
    A viewset for retrieving areas.
    """

    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    filterset_class = AreaFilterSet

    @extend_schema(
        parameters=[
            OpenApiParameter(name='geopage', location=OpenApiParameter.QUERY,
                             description='A page number within the paginated result set.', required=False, type=int),
            OpenApiParameter(name='page_size', location=OpenApiParameter.QUERY,
                             description='Number of results to return per page.', required=False, type=int),
        ],
    )
    @action(detail=False, url_path='geography', serializer_class=AreaGeoSerializer,
            pagination_class=LinkHeaderPagination)
    def geography(self, *args: list, **kwargs: dict) -> Response:
        """
        Retrieve a paginated list of area geographies.

        Returns a paginated response with area geographies.
        """
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
    A viewset for retrieving areas.

    Inherits from PublicAreasViewSet and adds authentication.
    """

    authentication_classes = (JWTAuthBackend, )
