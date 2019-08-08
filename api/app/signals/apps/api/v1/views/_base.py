"""
Viewset base classes, not to be used directly.
"""
from rest_framework.viewsets import GenericViewSet

from signals.apps.signals.models import Signal


class PublicSignalGenericViewSet(GenericViewSet):
    lookup_field = 'signal_id'
    lookup_url_kwarg = 'signal_id'

    queryset = Signal.objects.all()

    pagination_class = None
