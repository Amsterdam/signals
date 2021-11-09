# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import logging

from datapunt_api.rest import DatapuntViewSet, HALPagination
from django.conf import settings
from django.db import connection
from django.db.models import CharField, Value
from django.db.models.functions import JSONObject
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ViewSet

from signals.apps.api.app_settings import SIGNALS_API_GEO_PAGINATE_BY
from signals.apps.api.filters import SignalFilterSet, SignalPromotedToParentFilter
from signals.apps.api.generics import mixins
from signals.apps.api.generics.filters import FieldMappingOrderingFilter
from signals.apps.api.generics.pagination import LinkHeaderPagination
from signals.apps.api.generics.permissions import (
    SIAPermissions,
    SignalCreateInitialPermission,
    SignalViewObjectPermission
)
from signals.apps.api.renderers import SerializedJsonRenderer
from signals.apps.api.serializers import (
    AbridgedChildSignalSerializer,
    HistoryHalSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    PublicSignalCreateSerializer,
    PublicSignalSerializerDetail,
    SignalIdListSerializer
)
from signals.apps.api.serializers.signal_history import HistoryLogHalSerializer
from signals.apps.api.views._base import PublicSignalGenericViewSet
from signals.apps.history.models import Log
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal
from signals.apps.signals.models.aggregates.json_agg import JSONAgg
from signals.apps.signals.models.functions.asgeojson import AsGeoJSON
from signals.auth.backend import JWTAuthBackend
from signals.throttling import PostOnlyNoUserRateThrottle

logger = logging.getLogger(__name__)


class PublicSignalViewSet(PublicSignalGenericViewSet):
    throttle_classes = (PostOnlyNoUserRateThrottle,)
    serializer_class = PublicSignalSerializerDetail

    def list(self, *args, **kwargs):
        raise Http404

    def create(self, request):
        serializer = PublicSignalCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        signal = serializer.save()

        data = PublicSignalSerializerDetail(signal, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, uuid):
        signal = Signal.objects.get(uuid=uuid)

        data = PublicSignalSerializerDetail(signal, context=self.get_serializer_context()).data
        return Response(data)


class PublicSignalMapViewSet(ViewSet):
    renderer_classes = [SerializedJsonRenderer, BrowsableAPIRenderer]
    # django-drf has too much overhead with these kinds of 'fast' request.
    # When implemented using django-drf, retrieving a large number of elements cost around 4s (profiled)
    # Using pgsql ability to generate geojson, the request time reduces to 30ms (> 130x speedup!)
    # The downside is that this query has to be (potentially) maintained when changing one of the
    # following models: signal, categoryassignment, category, location, status

    def list(self, *args, **kwargs):
        fast_query = f"""
        select jsonb_build_object(
            'type', 'FeatureCollection',
            'features', json_agg(features.feature)
        ) as result from (
            select json_build_object(
                'type', 'Feature',
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
                and status.state not in ('{workflow.AFGEHANDELD}', '{workflow.AFGEHANDELD_EXTERN}', '{workflow.GEANNULEERD}', '{workflow.VERZOEK_TOT_HEROPENEN}')
            order by s.id desc
            limit 4000 offset 0
        ) as features
        """ # noqa

        cursor = connection.cursor()
        try:
            cursor.execute(fast_query)
            row = cursor.fetchone()
            return Response(row[0])
        except Exception as e:
            cursor.close
            logger.error('failed to retrieve signals json from db', exc_info=e)

    def get_view_name(self):
        # Overridden to avoid: "Public Signal Map List" that is the default behavior here.
        return 'Public Signal Map'


class PrivateSignalViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, DatapuntViewSet):
    """Viewset for `Signal` objects in private API"""
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
            return super().get_queryset(*args, **kwargs)
        else:
            qs = super().get_queryset(*args, **kwargs)
            return qs.filter_for_user(user=self.request.user)

    def check_object_permissions(self, request, obj):
        for permission_class in self.object_permission_classes:
            permission = permission_class()
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )

    @action(detail=True, url_path=r'history/?$')
    def history(self, *args, **kwargs):
        """
        History endpoint filterable by action.

        This function is used to switch between the signals_history_view or the history_log based history
        TODO: Replace with `history_log` when `history_view` has been deprecated
        """
        if settings.FEATURE_FLAGS.get('SIGNAL_HISTORY_LOG_ENABLED', False):
            return self.history_log(*args, **kwargs)
        return self.history_view(*args, **kwargs)

    @action(detail=True, url_path=r'history-view/?$')
    def history_view(self, *args, **kwargs):
        """
        History endpoint filterable by action.

        TODO: Deprecate in favour of `history_log`
        """
        signal = self.get_object()
        history_entries = signal.history.all()
        what = self.request.query_params.get('what', None)
        if what:
            history_entries = history_entries.filter(what=what)

        serializer = HistoryHalSerializer(history_entries, many=True)
        return Response(serializer.data)

    @action(detail=True, url_path=r'history-log/?$')
    def history_log(self, *args, **kwargs):
        """
        History endpoint filterable by action.

        TODO: Rename function to history when history_view has been deprecated
        """
        signal = self.get_object()
        history_log_qs = signal.history_log.all()

        what = self.request.query_params.get('what', None)
        if what:
            action = Log.translate_what_to_action(what)
            content_type = Log.translate_what_to_content_type(what)

            history_log_qs = history_log_qs.filter(action__iexact=action, content_type__model__iexact=content_type)

        serializer = HistoryLogHalSerializer(history_log_qs, many=True)
        return Response(serializer.data)

    @action(detail=False, url_path=r'geography/?$', filterset_class=SignalFilterSet)
    def geography(self, request):
        """
        SIG-3988

        To speed up the generation of the GeoJSON we are now skipping DRF serializers and are constructing the response
        in the database using the same type of query as used in the PublicSignalMapViewSet.list method.

        However we are not creating a raw query, instead we are creating the query in Django ORM and
        annotating/aggregating the result in the database. This way we keep all the benefits of the SignalFilterSet and
        the 'filter_for_user' functionality AND gain all the performance by skipping DRF and letting the database
        generate the GeoJSON.
        """
        feature_collection = {
            'type': 'FeatureCollection'
        }

        feature_collection.update(self.filter_queryset(
            self.geography_queryset.annotate(
                feature=JSONObject(
                    type=Value('Feature', output_field=CharField()),
                    geometry=AsGeoJSON('location__geometrie'),
                    properties=JSONObject(
                        id='id',
                        created_at='created_at',
                    ),
                )
            ).filter_for_user(
                user=request.user
            )
        ).aggregate(
            features=JSONAgg('feature')
        ))

        headers = []
        paginator = LinkHeaderPagination(page_query_param='geopage', page_size=SIGNALS_API_GEO_PAGINATE_BY)
        page = paginator.paginate_queryset(feature_collection['features'], self.request, view=self)
        if page is not None:
            feature_collection['features'] = page
            headers = paginator.get_pagination_headers()

        return Response(feature_collection, headers=headers)

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
        if signal.is_child:
            raise NotFound(detail=f'Signal {pk} has no children, it itself is a child signal.')
        elif not signal.is_parent:
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


class SignalPromotedToParentViewSet(GenericViewSet, mixins.ListModelMixin):
    serializer_class = SignalIdListSerializer
    pagination_class = HALPagination

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = SignalPromotedToParentFilter

    queryset = Signal.objects.prefetch_related('children').only('id').filter(children__isnull=False).order_by('-id')
