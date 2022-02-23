# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
import logging

from django.db.models import CharField, Value
from django.db.models.functions import Coalesce, JSONObject
from django.http import Http404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from signals.apps.api.app_settings import SIGNALS_API_GEO_PAGINATE_BY
from signals.apps.api.generics.pagination import LinkHeaderPaginationForQuerysets
from signals.apps.api.serializers import PublicSignalCreateSerializer, PublicSignalSerializerDetail
from signals.apps.signals.models import Signal
from signals.apps.signals.models.aggregates.json_agg import JSONAgg
from signals.apps.signals.models.functions.asgeojson import AsGeoJSON
from signals.apps.signals.workflow import (
    AFGEHANDELD,
    AFGEHANDELD_EXTERN,
    GEANNULEERD,
    VERZOEK_TOT_HEROPENEN
)
from signals.throttling import PostOnlyNoUserRateThrottle

logger = logging.getLogger(__name__)


class PublicSignalViewSet(GenericViewSet):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Signal.objects.select_related(
        'category_assignment',
        'category_assignment__category',
        'location',
        'status',
    ).all()

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

    @action(detail=False, url_path=r'geography/?$', methods=['GET'])
    def geography(self, request):
        """
        Returns a GeoJSON of all Signal's that are in an "Open" state and in a publicly available category.
        Additional filtering can be done by adding query parameters.

        TODO:
        - Determine the properties that must be returned
        - Add filtering by category
        - Add filtering by BBOX
        """
        queryset = self.filter_queryset(
            self.get_queryset().annotate(
                # This will transform the output of the query to GeoJSON instead of using a Serializer
                feature=JSONObject(
                    type=Value('Feature', output_field=CharField()),
                    geometry=AsGeoJSON('location__geometrie'),
                    properties=JSONObject(
                        category=JSONObject(
                            # Return the category public_name. If the public_name is empty, return the category name
                            name=Coalesce('category_assignment__category__public_name',
                                          'category_assignment__category__name'),
                        ),
                        # Creation date of the Signal
                        created_at='created_at',
                    ),
                )
            )
        ).exclude(
            # All signals that are in an "Open" state
            status__state__in=[AFGEHANDELD, AFGEHANDELD_EXTERN, GEANNULEERD, VERZOEK_TOT_HEROPENEN],

            # Only return Signal's that are in categories that are publicly accessible
            category_assignment__category__is_public_accessible=True,
        ).order_by(
            # Newest signals first
            '-created_at',
        )

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