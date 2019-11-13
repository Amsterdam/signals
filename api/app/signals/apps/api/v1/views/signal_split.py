"""
ViewSet that splits `api.Signal` instances in several children.
"""
from rest_framework import viewsets

from signals.apps.api import mixins
from signals.apps.api.generics.permissions import SplitPermission
from signals.apps.api.v1.serializers import PrivateSplitSignalSerializer
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend


class PrivateSignalSplitViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    serializer_class = PrivateSplitSignalSerializer
    queryset = Signal.objects.all()
    pagination_class = None

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SplitPermission,)
