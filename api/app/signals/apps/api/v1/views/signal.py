from datapunt_api.rest import DatapuntViewSet, HALPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.api import mixins
from signals.apps.api.generics.filters import FieldMappingOrderingFilter
from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.v1.filters import SignalFilter
from signals.apps.api.v1.serializers import (
    HistoryHalSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    PublicSignalCreateSerializer,
    PublicSignalSerializerDetail
)
from signals.apps.api.v1.views._base import PublicSignalGenericViewSet
from signals.apps.signals.models import History, Signal
from signals.auth.backend import JWTAuthBackend


class PublicSignalViewSet(CreateModelMixin, DetailSerializerMixin, RetrieveModelMixin,
                          PublicSignalGenericViewSet):
    serializer_class = PublicSignalCreateSerializer
    serializer_detail_class = PublicSignalSerializerDetail


class PrivateSignalViewSet(DatapuntViewSet,
                           mixins.CreateModelMixin,
                           mixins.UpdateModelMixin):
    """Viewset for `Signal` objects in V1 private API"""
    queryset = Signal.objects.select_related(
        'location',
        'status',
        'category_assignment',
        'category_assignment__category__parent',
        'reporter',
        'priority',
        'parent',
    ).prefetch_related(
        'category_assignment__category__departments',
        'children',
        'attachments',
        'notes',
    ).all()

    serializer_class = PrivateSignalSerializerList
    serializer_detail_class = PrivateSignalSerializerDetail

    pagination_class = HALPagination

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    filter_backends = (DjangoFilterBackend, FieldMappingOrderingFilter, )
    filterset_class = SignalFilter

    ordering = ('-created_at', )
    ordering_fields = (
        'id',
        'created_at',
        'updated_at',
        'stadsdeel',
        'sub_category',
        'main_category',
        'status',
        'priority',
        'address',
    )
    ordering_field_mappings = {
        'id': 'id',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
        'stadsdeel': 'location__stadsdeel',
        'sub_category': 'category_assignment__category__slug',
        'main_category': 'category_assignment__category__parent__slug',
        'status': 'status__state',
        'priority': 'priority__priority',
        'address': 'location__address_text',
    }

    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'trace']

    @action(detail=True)
    def history(self, request, pk=None):
        """History endpoint filterable by action."""
        history_entries = History.objects.filter(_signal__id=pk)
        what = self.request.query_params.get('what', None)
        if what:
            history_entries = history_entries.filter(what=what)

        serializer = HistoryHalSerializer(history_entries, many=True)
        return Response(serializer.data)
