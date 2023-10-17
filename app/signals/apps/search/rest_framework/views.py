# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from typing import Optional

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from elasticsearch_dsl.query import MultiMatch
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.api.generics.exceptions import GatewayTimeoutException
from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.serializers import PrivateSignalSerializerDetail, PrivateSignalSerializerList
from signals.apps.search.documents.signal import SignalDocument
from signals.apps.search.elasticsearch_dsl.search import StatusMessagesSearch
from signals.apps.search.rest_framework.pagination import ElasticHALPagination
from signals.apps.search.rest_framework.serializers import StatusMessageListSerializer
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend
from signals.schema import GenericErrorSerializer


class SearchView(DetailSerializerMixin, ReadOnlyModelViewSet):
    authentication_classes = [JWTAuthBackend]
    permission_classes = (SIAPermissions,)

    serializer_class = PrivateSignalSerializerList
    serializer_detail_class = PrivateSignalSerializerDetail

    queryset = Signal.objects.none()

    pagination_class = ElasticHALPagination

    ordering_fields: tuple[str] = (
        'created_at',
    )

    def _validate_ordering(self, ordering: list[str]) -> None:
        for field in ordering:
            name = field
            if field[0] == '-':
                name = field[1:]

            if name not in self.ordering_fields:
                raise ValidationError({'ordering': f"Cannot order by '{field}'!"})

    def get_queryset(self, *args, **kwargs):
        q = self.request.query_params.get('q', '')

        multi_match = MultiMatch(
            query=q,
            fields=[
                'id',
                'text',
                'category_assignment.category.name',
                'reporter.email',  # SIG-2058 [BE] email, telefoon aan vrij zoeken toevoegen
                'reporter.phone'  # SIG-2058 [BE] email, telefoon aan vrij zoeken toevoegen
            ],
            zero_terms_query='all',
        )

        s = SignalDocument.search().query(multi_match)

        ordering = self.request.query_params.get('ordering')
        if ordering is not None:
            ordering = ordering.split(',')
            self._validate_ordering(ordering)
            s = s.sort(*ordering)

        s.execute()
        return s

    @extend_schema(
        parameters=[
            OpenApiParameter('q', OpenApiTypes.STR, description='The search term.'),
            OpenApiParameter('ordering', OpenApiTypes.STR, description='Order the results by a specific field. '
                                                                       'Currently the only valid options are '
                                                                       '"created_at" and "-created_at".'),
        ],
        responses={
            200: PrivateSignalSerializerList,
            400: OpenApiTypes.OBJECT,
            401: GenericErrorSerializer,
            403: GenericErrorSerializer,
            500: GenericErrorSerializer,
        },
        examples=[
            OpenApiExample(
                'Bad Request',
                description='When providing a field name that is not supported by the "ordering" parameter.',
                value={'ordering': "Cannot order by 'updated_at'!}"},
                status_codes=['400'],
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        if not SignalDocument.ping():
            raise GatewayTimeoutException(detail='The elastic cluster is unreachable')
        return super().list(request=request, *args, **kwargs)


class StatusMessageSearchView(APIView):
    """View providing support for searching for status messages using elasticsearch."""
    authentication_classes = [JWTAuthBackend]
    permission_classes = (SIAPermissions,)
    # serializer_class is defined so that drf-spectacular can find out which serializer belongs with this view
    serializer_class = StatusMessageListSerializer

    @extend_schema(parameters=[
        OpenApiParameter('q', OpenApiTypes.STR, description='The search term.'),
        OpenApiParameter(
            'state',
            OpenApiTypes.STR,
            description='Filter the search results on state code '
                        '(add parameter to querystring multiple times to filter on multiple states).'
        ),
        OpenApiParameter(
            'active',
            OpenApiTypes.BOOL,
            description='Filter the search results on the "active" state of the status message.'
        ),
        OpenApiParameter('page_size', OpenApiTypes.INT, description='Number of results returned per page.'),
        OpenApiParameter('page', OpenApiTypes.INT, description='The page number of the paginated results.'),
    ])
    def get(self, request: Request, format: Optional[str] = None) -> Response:
        """This will perform a lookup using elasticsearch using a "fuzzy" search, which allows
        for typos, misspelling, pluralization, etc...
        It allows for filtering based on the 'state' key and by the 'active' state by using
        querystring parameters 'state' and 'active' respectively.
        When no search term is provided using querystring parameter 'q', all status messages
        will be returned (optionally filtered using the 'state' and 'active' filters).
        When a search term is provided a 'highlight' section is available for both the 'title'
        and 'text' field, which can be used to display the title and text of the status messages
        in the results with the search term highlighted.
        Pagination is provided using the 'page_size' and 'page' querystring parameters.
        In the results there is a 'facets' section available, which provides counts for every
        filter option.
        """
        q = ''
        if 'q' in request.query_params:
            q = request.query_params['q']

        filters = {}
        if 'state' in request.query_params:
            filters['state'] = request.query_params.getlist('state')

        if 'active' in request.query_params:
            filters['active'] = request.query_params['active']

        end = 15
        if 'page_size' in request.query_params:
            end = int(request.query_params['page_size'])

        start = 0
        if 'page' in request.query_params:
            page = int(request.query_params['page']) - 1
            if page < 0:
                return Response({'detail': 'Ongeldige pagina.'}, 404)

            start = page * end
            end = start + end

        search = StatusMessagesSearch(q, filters)[start:end]

        response = search.execute()
        serializer = StatusMessageListSerializer(response)

        return Response(data=serializer.data)
