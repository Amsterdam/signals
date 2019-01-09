"""
Views that are used exclusively by the V0 API
"""
from datapunt_api.rest import DatapuntViewSet

from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend

from .serializers import SignalZDSSerializer


class SignalZDSViewSet(DatapuntViewSet):
    authentication_classes = []
    permission_classes = []
    queryset = Signal.objects.order_by('-created_at')
    serializer_detail_class = SignalZDSSerializer
    serializer_class = SignalZDSSerializer
