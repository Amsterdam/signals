from datapunt_api.rest import DatapuntViewSet
from elasticsearch_dsl.query import MultiMatch

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.v1.serializers import (
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList
)
from signals.apps.search.documents.signal import SignalDocument
from signals.apps.search.pagination import ElasticHALPagination
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
