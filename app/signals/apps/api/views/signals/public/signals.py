# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from typing import Any

from django.db.models import Min, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from signals.apps.api.app_settings import SIGNALS_API_GEO_PAGINATE_BY
from signals.apps.api.filters.signal import PublicSignalGeographyFilter
from signals.apps.api.generics.pagination import LinkHeaderPaginationForQuerysets
from signals.apps.api.serializers import PublicSignalCreateSerializer, PublicSignalSerializerDetail
from signals.apps.signals.models import Signal
from signals.apps.signals.models.aggregates.json_agg import JSONAgg
from signals.apps.signals.models.views.signal import PublicSignalGeographyFeature
from signals.apps.signals.workflow import (
    AFGEHANDELD,
    AFGEHANDELD_EXTERN,
    GEANNULEERD,
    GESPLITST,
    VERZOEK_TOT_HEROPENEN
)
from signals.throttling import PostOnlyNoUserRateThrottle


class PublicSignalViewSet(CreateModelMixin, RetrieveModelMixin, GenericViewSet):
    """ViewSet for public signals."""
    lookup_field: str = 'uuid'
    lookup_url_kwarg: str = 'uuid'

    queryset = Signal.objects.all()
    geography_queryset = PublicSignalGeographyFeature.objects.all()

    filter_backends: tuple = ()
    filterset_class: Any = None
    ordering: Any = None
    ordering_fields: Any = None
    pagination_class: Any = None
    serializer_class = PublicSignalSerializerDetail
    throttle_classes: tuple = (PostOnlyNoUserRateThrottle, )

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:

        """
        Create a signal.

        Args:
            request: The request object.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            A Response containing the created signal data that can be shared publicly.

        Raises:
            Exception: If the serializer validation fails.

        """
        serializer = PublicSignalCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        signal = serializer.save()

        data = PublicSignalSerializerDetail(signal, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, url_path=r'geography/?$', methods=['GET'],
            filter_backends=(DjangoFilterBackend, OrderingFilter), filterset_class=PublicSignalGeographyFilter,
            ordering=('-created_at', ), ordering_fields=('created_at', ), queryset=geography_queryset)
    def geography(self, request: Request) -> Response:
        """
        Retrieve a GeoJSON representation of signals that can be shared on a public map.

        Args:
            request: The request object.

        Returns:
            A Response containing the paginated GeoJSON feature collection.

        """
        queryset = self.filter_queryset(
            self.get_queryset().exclude(
                Q(state__in=[AFGEHANDELD, AFGEHANDELD_EXTERN, GEANNULEERD, GESPLITST, VERZOEK_TOT_HEROPENEN]) |
                ~Q(child_category_is_public_accessible=True)
            )
        ).order_by('geometry')

        if request.query_params.get('group_by', '').lower() == 'category':
            # Group by category and return the oldest signal created_at date
            queryset = queryset.values('child_category_id').annotate(created_at=Min('created_at'))

        # Paginate our queryset and turn it into a GeoJSON feature collection:
        headers = []
        feature_collection = {'type': 'FeatureCollection', 'features': []}
        paginator = LinkHeaderPaginationForQuerysets(page_query_param='geopage', page_size=SIGNALS_API_GEO_PAGINATE_BY)
        page_qs = paginator.paginate_queryset(queryset, self.request, view=self)

        if page_qs is not None:
            features = page_qs.aggregate(features=JSONAgg('feature'))
            feature_collection.update(features)
            headers = paginator.get_pagination_headers()

        return Response(feature_collection, headers=headers)
