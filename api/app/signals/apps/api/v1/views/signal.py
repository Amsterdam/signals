from datapunt_api.rest import DatapuntViewSet, HALPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from signals.apps.api import mixins
from signals.apps.api.generics.filters import FieldMappingOrderingFilter
from signals.apps.api.generics.pagination import LinkHeaderPagination
from signals.apps.api.generics.permissions import SignalCreateInitialPermission
from signals.apps.api.generics.permissions.base import SignalViewObjectPermission
from signals.apps.api.v1.filters import SignalFilter
from signals.apps.api.v1.serializers import (
    HistoryHalSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    PublicSignalCreateSerializer,
    PublicSignalSerializerDetail,
    SignalGeoSerializer
)
from signals.apps.api.v1.views._base import PublicSignalGenericViewSet
from signals.apps.signals.models import History, Signal
from signals.auth.backend import JWTAuthBackend


class PublicSignalViewSet(PublicSignalGenericViewSet):
    def create(self, request):
        serializer = PublicSignalCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        signal = serializer.save()

        data = PublicSignalSerializerDetail(signal, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, signal_id):
        signal = Signal.objects.get(signal_id=signal_id)

        data = PublicSignalSerializerDetail(signal, context=self.get_serializer_context()).data
        return Response(data)


class PrivateSignalViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, DatapuntViewSet):
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

    # Geography queryset to reduce the complexity of the query
    geography_queryset = Signal.objects.select_related(
        'location',  # We only need the location for now
    ).filter(
        location__isnull=False  # We can only show signals on a map that have a location
    ).only(  # No need to select anything else than the id, created and the location for now
        'id',
        'created_at',
        'location'
    ).all()

    serializer_class = PrivateSignalSerializerList
    serializer_detail_class = PrivateSignalSerializerDetail

    pagination_class = HALPagination

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SignalCreateInitialPermission,)
    object_permission_classes = (SignalViewObjectPermission, )

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

    def get_queryset(self, *args, **kwargs):
        if self._is_request_to_detail_endpoint():
            return super(PrivateSignalViewSet, self).get_queryset(*args, **kwargs)
        else:
            qs = super(PrivateSignalViewSet, self).get_queryset(*args, **kwargs)
            return qs.filter_for_user(user=self.request.user)

    def check_object_permissions(self, request, obj):
        for permission_class in self.object_permission_classes:
            permission = permission_class()
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )

    @action(detail=True)
    def history(self, request, pk=None):
        """History endpoint filterable by action."""
        history_entries = History.objects.filter(_signal__id=pk)
        what = self.request.query_params.get('what', None)
        if what:
            history_entries = history_entries.filter(what=what)

        serializer = HistoryHalSerializer(history_entries, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def geography(self, request):
        # Makes use of the optimised queryset
        filtered_qs = self.filter_queryset(
            self.geography_queryset.filter_for_user(
                user=self.request.user
            )
        ).order_by(
            'id'  # Oldest Signals first
        )

        paginator = LinkHeaderPagination(page_query_param='geopage', page_size=4000)  # noqa page_size = 2.5 times the average signals made in a day, at this moment the highest average is 1600
        page = paginator.paginate_queryset(filtered_qs, self.request, view=self)
        if page is not None:
            serializer = SignalGeoSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SignalGeoSerializer(filtered_qs, many=True)
        return Response(serializer.data)
