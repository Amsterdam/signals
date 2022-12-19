# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import logging

from datapunt_api.rest import DEFAULT_RENDERERS
from django.db.models import CharField, Value
from django.db.models.functions import JSONObject
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from signals.apps.api.generics.pagination import LinkHeaderPaginationForQuerysets
from signals.apps.gisib import app_settings
from signals.apps.gisib.models import GISIBFeature
from signals.apps.gisib.rest_framework.filters.feature_collection import FeatureCollectionFilterSet
from signals.apps.signals.models.aggregates.json_agg import JSONAgg
from signals.apps.signals.models.functions.asgeojson import AsGeoJSON

logger = logging.getLogger(__name__)


class PublicGISIBFeatureCollectionViewSet(GenericViewSet):
    authentication_classes = ()
    renderer_classes = DEFAULT_RENDERERS

    queryset = GISIBFeature.objects.all()

    filter_backends = (DjangoFilterBackend, )
    filterset_class = FeatureCollectionFilterSet

    @action(detail=False, url_path=r'quercus/?$', methods=['GET'])
    def quercus(self, *args, **kwargs):
        """
        Return a GeoJSON Feature Collection of Oak trees "Quercus". Can be filtered on bounding box.
        """
        features_qs = self.filter_queryset(
            self.get_queryset().filter(
                properties__object__latin__istartswith='Quercus'
            ).annotate(
                feature=JSONObject(
                    type=Value('Feature', output_field=CharField()),
                    id='gisib_id',
                    geometry=AsGeoJSON('geometry'),
                    properties='properties',
                )
            )
        ).order_by('-geometry')

        # Paginate our queryset and turn it into a GeoJSON feature collection:
        headers = []
        feature_collection = {'type': 'FeatureCollection', 'features': []}
        paginator = LinkHeaderPaginationForQuerysets(page_query_param='geopage', page_size=app_settings.PAGE_SIZE)
        page_qs = paginator.paginate_queryset(features_qs, self.request, view=self)

        if page_qs is not None:
            features = page_qs.aggregate(features=JSONAgg('feature'))
            feature_collection.update(features)
            headers = paginator.get_pagination_headers()

        return Response(feature_collection, status=200, headers=headers)
