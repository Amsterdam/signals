import logging

from datapunt_api.rest import DatapuntViewSet, HALPagination
from django.db import connection
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from signals.apps.api.generics import mixins
from signals.apps.api.generics.filters import FieldMappingOrderingFilter
from signals.apps.api.generics.pagination import LinkHeaderPagination
from signals.apps.api.generics.permissions import (
    SignalCreateInitialPermission,
    SignalViewObjectPermission
)
from signals.apps.api.v1.filters import SignalFilterSet
from signals.apps.api.v1.serializers import (
    AbridgedChildSignalSerializer,
    HistoryHalSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    PublicSignalCreateSerializer,
    PublicSignalSerializerDetail,
    SignalGeoSerializer
)
from signals.apps.api.v1.views._base import PublicSignalGenericViewSet
from signals.apps.signals import workflow
from signals.apps.signals.models import History, Signal
from signals.auth.backend import JWTAuthBackend

logger = logging.getLogger(__name__)


class PublicSignalViewSet(PublicSignalGenericViewSet):
    serializer_class = PublicSignalSerializerDetail

    def list(self, *args, **kwargs):
        raise Http404

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


class PublicSignalListViewSet(PublicSignalGenericViewSet):
    # django-drf has too much overhead these kinds of 'fast' request.
    # When implemented using django-drf, retrieving a large number of elements cost around 4s (profiled)
    # Using pgsql ability to generate geojson, the request time reduces to 30ms (> 130x speedup!)
    # The downside is that this query has to be (potentially) maintained when changing one of the
    # following models: sginal, categoryassignment, category, location, status
    def list(self, *args, **kwargs):
        fast_query = f"""
        select jsonb_build_object(
            'type', 'FeatureCollection',
            'features', json_agg(features.feature)
        ) as result from (
            select json_build_object(
                'type', 'feature',
                'geometry', st_asgeojson(l.geometrie)::jsonb,
                'properties', json_build_object(
                    'id', to_jsonb(s.id),
                    'created_at', to_jsonb(s.created_at),
                    'status', to_jsonb(status.state),
                    'category', json_build_object(
                        'sub', to_jsonb(cat.name),
                        'main', to_jsonb(maincat.name)
                    )
                )
            ) as feature
            from
                signals_signal s
                left join signals_categoryassignment ca on s.category_assignment_id = ca.id
                left join signals_category cat on ca.category_id = cat.id
                left join signals_category maincat on cat.parent_id = maincat.id,
                signals_location l,
                signals_status status
            where
                s.location_id = l.id
                and s.status_id = status.id
                and status.state not in ('{workflow.AFGEHANDELD}', '{workflow.AFGEHANDELD_EXTERN}')
            order by s.id desc
            limit 4000 offset 0
        ) as features
        """

        cursor = connection.cursor()
        try:
            cursor.execute(fast_query)
            row = cursor.fetchone()
            return Response(row)
        except Exception as e:
            cursor.close
            logger.error('failed to retrieve signals json from db', exc_info=e)

    def create(self, request):
        # this endpoint only returns list, and is not intended to be used for other purposes
        raise Http404

    def retrieve(self, request, signal_id):
        # this endpoint only returns list, and is not intended to be used for other purposes
        raise Http404


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
        'type_assignment',
    ).prefetch_related(
        'category_assignment__category__departments',
        'children',
        'attachments',
        'notes',
        'signal_departments',
        'user_assignment',
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
    filterset_class = SignalFilterSet

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
        'assigned_user_email',
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
        'assigned_user_email': 'user_assignment__user__email',
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

    @action(detail=True, url_path=r'history/?$')
    def history(self, request, pk=None):
        """History endpoint filterable by action."""
        history_entries = History.objects.filter(_signal__id=pk)
        what = self.request.query_params.get('what', None)
        if what:
            history_entries = history_entries.filter(what=what)

        serializer = HistoryHalSerializer(history_entries, many=True)
        return Response(serializer.data)

    @action(detail=False, url_path=r'geography/?$')
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

    @action(detail=True, url_path=r'children/?$')
    def children(self, request, pk=None):
        """Show abbriged version of child signals for a given parent signal."""
        # Based on a user's department a signal may not be accessible.
        signal_exists = Signal.objects.filter(id=pk).exists()
        signal_accessible = Signal.objects.filter_for_user(request.user).filter(id=pk).exists()

        if signal_exists and not signal_accessible:
            raise PermissionDenied()

        # return a HTTP 404 if we ask for a child signal's children.
        signal = self.get_object()
        if signal.is_child():
            raise NotFound(detail=f'Signal {pk} has no children, it itself is a child signal.')
        elif not signal.is_parent():
            raise NotFound(detail=f'Signal {pk} has no children.')

        # Return the child signals for a parent signal in an abridged version
        # of the usual serialization.
        paginator = HALPagination()
        child_qs = signal.children.all()
        page = paginator.paginate_queryset(child_qs, self.request, view=self)

        if page is not None:
            serializer = AbridgedChildSignalSerializer(page, many=True, context=self.get_serializer_context())
            return paginator.get_paginated_response(serializer.data)

        serializer = AbridgedChildSignalSerializer(child_qs, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, (list, )):
            serializer = self.get_serializer(data=request.data, many=True)
        else:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
