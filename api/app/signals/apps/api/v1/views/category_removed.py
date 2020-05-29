"""
ViewSet that returns `signals.Signal` instance dropped out of a category.
"""
from datapunt_api.rest import HALPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from signals.apps.api.generics import mixins
from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.v1.filters import SignalCategoryRemovedAfterFilter
from signals.apps.api.v1.serializers import SignalIdListSerializer
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend


class SignalCategoryRemovedAfterViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SignalIdListSerializer
    pagination_class = HALPagination

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = SignalCategoryRemovedAfterFilter

    queryset = Signal.objects.only('id').all()
