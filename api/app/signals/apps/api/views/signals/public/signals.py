# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from django.db.models import Min, Q
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
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
    VERZOEK_TOT_HEROPENEN
)
from signals.throttling import PostOnlyNoUserRateThrottle


class PublicSignalViewSet(GenericViewSet):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Signal.objects.all()

    # A queryset based on a materialized view that can quickly provide the information needed for the
    # geography endpoint
    geography_queryset = PublicSignalGeographyFeature.objects.exclude(
        # Only signals that are in an "Open" state
        Q(state__in=[AFGEHANDELD, AFGEHANDELD_EXTERN, GEANNULEERD, VERZOEK_TOT_HEROPENEN])
    )

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = None
    ordering = None
    ordering_fields = None

    pagination_class = None
    serializer_class = PublicSignalSerializerDetail

    throttle_classes = (PostOnlyNoUserRateThrottle,)

    def list(self, *args, **kwargs):
        raise Http404

    def create(self, request):
        serializer = PublicSignalCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        signal = serializer.save()

        data = PublicSignalSerializerDetail(signal, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, uuid):
        signal = get_object_or_404(Signal.objects.all(), uuid=uuid)
        data = PublicSignalSerializerDetail(signal, context=self.get_serializer_context()).data
        return Response(data)

    @action(detail=False, url_path=r'geography/?$', methods=['GET'], filterset_class=PublicSignalGeographyFilter,
            ordering=('-created_at', ), ordering_fields=('created_at', ), queryset=geography_queryset)
    def geography(self, request) -> Response:
        """
        Returns a GeoJSON of all Signal's that are in an "Open" state and in a publicly available category.
        Additional filtering can be done by adding query parameters.

        This endpoint uses a materialized view in the database that can quickly provide the information needed
        """
        queryset = self.filter_queryset(
            self.get_queryset()
        ).exclude(
            child_category_is_public_accessible=False
        ).order_by(
            'geometry'
        )

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
