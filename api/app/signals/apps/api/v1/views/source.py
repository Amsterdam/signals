from datapunt_api.rest import DatapuntViewSet

from signals.apps.api.v1.serializers.source import SourceSerializer
from signals.apps.signals.models import Source
from signals.auth.backend import JWTAuthBackend


class PrivateSourcesViewSet(DatapuntViewSet):
    """
    V1 Private ViewSet to display all sources in the database
    """
    serializer_class = SourceSerializer
    serializer_detail_class = SourceSerializer

    queryset = Source.objects.all()

    authentication_classes = (JWTAuthBackend, )
