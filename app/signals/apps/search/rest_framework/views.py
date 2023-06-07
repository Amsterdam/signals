# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
from typing import Optional

from datapunt_api.rest import DatapuntViewSet
from elasticsearch_dsl import FacetedSearch, Search, TermsFacet
from elasticsearch_dsl.query import MultiMatch
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from signals.apps.api.generics.exceptions import GatewayTimeoutException
from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.serializers import PrivateSignalSerializerDetail, PrivateSignalSerializerList
from signals.apps.search.documents.signal import SignalDocument
from signals.apps.search.documents.status_message import StatusMessage
from signals.apps.search.rest_framework.pagination import ElasticHALPagination
from signals.apps.search.rest_framework.serializers import StatusMessageListSerializer
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend


class SearchView(DatapuntViewSet):
    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    serializer_class = PrivateSignalSerializerList
    serializer_detail_class = PrivateSignalSerializerDetail

    queryset = Signal.objects.none()

    pagination_class = ElasticHALPagination

    def get_queryset(self, *args, **kwargs):
        if 'q' in self.request.query_params:
            q = self.request.query_params['q']
        else:
            q = '*'

        multi_match = MultiMatch(
            query=q,
            fields=[
                'id',
                'text',
                'category_assignment.category.name',
                'reporter.email',  # SIG-2058 [BE] email, telefoon aan vrij zoeken toevoegen
                'reporter.phone'  # SIG-2058 [BE] email, telefoon aan vrij zoeken toevoegen
            ]
        )

        s = SignalDocument.search().query(multi_match)
        s.execute()
        return s

    def list(self, request, *args, **kwargs):
        if not SignalDocument.ping():
            raise GatewayTimeoutException(detail='The elastic cluster is unreachable')
        return super().list(request=request, *args, **kwargs)


class StatusMessagesSearch(FacetedSearch):
    """The Elasticsearch DSL library requires us to subclass FacetedSearch in order to
    configure a faceted search, which allows us to use filters and provides us with
    counts for each possible filter option.
    """
    index = 'status_messages'
    doc_types = (StatusMessage,)
    fields = ('title', 'text',)
    facets = {
        'state': TermsFacet(field='state', size=20, min_doc_count=0),
        'active': TermsFacet(field='active', min_doc_count=0),
    }

    def query(self, search: Search, query: str):
        """Overridden query method in order to set the fuzziness of the query and
        to provide the zero_terms_query option in order to get (all) results when
        no query term is provided.
        """
        return search.query(
            'multi_match',
            query=query,
            fields=self.fields,
            fuzziness='AUTO',
            zero_terms_query='all',
        )


class StatusMessageSearchView(APIView):
    """View providing support for searching for status messages using elasticsearch."""
    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

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
