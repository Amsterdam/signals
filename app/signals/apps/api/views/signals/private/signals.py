# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
import logging

from django.conf import settings
from django.db.models import CharField, Value
from django.db.models.functions import JSONObject
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.api.filters import SignalFilterSet
from signals.apps.api.generics.filters import FieldMappingOrderingFilter
from signals.apps.api.generics.pagination import HALPagination, LinkHeaderPaginationForQuerysets
from signals.apps.api.generics.permissions import (
    SignalCreateInitialPermission,
    SignalViewObjectPermission
)
from signals.apps.api.serializers import (
    AbridgedChildSignalSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList
)
from signals.apps.api.serializers.email_preview import (
    EmailPreviewPostSerializer,
    EmailPreviewSerializer
)
from signals.apps.api.serializers.signal_history import HistoryLogHalSerializer
from signals.apps.email_integrations.utils import trigger_mail_action_for_email_preview
from signals.apps.history.models import Log
from signals.apps.services.domain.pdf import PDFSummaryService
from signals.apps.signals.models import Signal
from signals.apps.signals.models.aggregates.json_agg import JSONAgg
from signals.apps.signals.models.functions.asgeojson import AsGeoJSON
from signals.auth.backend import JWTAuthBackend

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(responses={HTTP_200_OK: PrivateSignalSerializerList(many=True)},
                       description='List of signals'),
    create=extend_schema(responses={HTTP_201_CREATED: PrivateSignalSerializerList},
                         description='Create a new signal'),
    retrieve=extend_schema(responses={HTTP_200_OK: PrivateSignalSerializerDetail},
                           description='Retrieve a signal'),
    update=extend_schema(responses={HTTP_200_OK: PrivateSignalSerializerDetail},
                         description='Update a signal'),
    partial_update=extend_schema(responses={HTTP_200_OK: PrivateSignalSerializerDetail},
                                 description='Partial update a signal'),
)
class PrivateSignalViewSet(DetailSerializerMixin, CreateModelMixin, UpdateModelMixin, ReadOnlyModelViewSet):
    """Viewset for `Signal` objects in private API"""
    queryset = Signal.objects.select_related(
        'location',
        'status',
        'category_assignment',
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
    )

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

    authentication_classes = [JWTAuthBackend]
    permission_classes = (SignalCreateInitialPermission, )
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
        'area_name',
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
        'area_name': 'location__area_name',
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

    @extend_schema(
        parameters=[OpenApiParameter('what', OpenApiTypes.STR, description='Filters a specific "action"')],
        responses={HTTP_200_OK: HistoryLogHalSerializer(many=True)}
    )
    @action(detail=True, url_path='history', filterset_class=None, filter_backends=(), pagination_class=None)
    def history(self, *args, **kwargs):
        """
        History endpoint filterable by action.
        """
        signal = self.get_object()
        history_log_qs = signal.history_log.all()

        what = self.request.query_params.get('what', None)
        if what:
            action = Log.translate_what_to_action(what)
            content_type = Log.translate_what_to_content_type(what)

            # TODO: Fix this properly
            if action == 'RECEIVE' and content_type == 'feedback':
                action = 'CREATE'

            history_log_qs = history_log_qs.filter(action__iexact=action, content_type__model__iexact=content_type)

        serializer = HistoryLogHalSerializer(history_log_qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        responses={
            HTTP_200_OK: {
                'type': 'object',
                'properties': {
                    'type': {
                        'type': 'string',
                        'enum': [
                            'FeatureCollection'
                        ],
                        'example': 'FeatureCollection'
                    },
                    'features': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'type': {
                                    'type': 'string',
                                    'enum': [
                                        'Feature'
                                    ],
                                    'example': 'Feature'
                                },
                                'geometry': {
                                    'type': 'object',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'enum': [
                                                'Point'
                                            ]
                                        },
                                        'coordinates': {
                                            'type': 'array',
                                            'items': {
                                                'type': 'number'
                                            },
                                            'example': [
                                                4.890659,
                                                52.373069
                                            ]
                                        }
                                    }
                                },
                                'properties': {
                                    'type': 'object',
                                    'properties': {
                                        'id': {
                                            'type': 'integer',
                                            'example': 1
                                        },
                                        'created_at': {
                                            'type': 'string',
                                            'format': 'date-time',
                                            'example': '2023-06-01T00:00:00.000000+00:00'
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        description='GeoJSON of all signals',
    )
    @action(detail=False, url_path='geography', filterset_class=SignalFilterSet)
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
        # Annotate Signal queryset with GeoJSON features and filter it according
        # to "Signalen" project access rules:
        features_qs = self.filter_queryset(
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
        )

        # Paginate our queryset and turn it into a GeoJSON feature collection:
        headers = []
        feature_collection = {'type': 'FeatureCollection', 'features': []}
        paginator = LinkHeaderPaginationForQuerysets(page_query_param='geopage',
                                                     page_size=settings.SIGNALS_API_GEO_PAGINATE_BY)
        page_qs = paginator.paginate_queryset(features_qs, self.request, view=self)

        if page_qs is not None:
            features = page_qs.aggregate(features=JSONAgg('feature'))
            feature_collection.update(features)
            headers = paginator.get_pagination_headers()

        return Response(feature_collection, headers=headers)

    @extend_schema(responses={HTTP_200_OK: AbridgedChildSignalSerializer(many=True)})
    @action(detail=True, url_path='children', filterset_class=None, filter_backends=())
    def children(self, request, pk=None):
        """Show abridged version of child signals for a given parent signal."""
        # Based on a user's department a signal may not be accessible.
        signal_exists = Signal.objects.filter(id=pk).exists()
        signal_accessible = Signal.objects.filter_for_user(request.user).filter(id=pk).exists()

        if signal_exists and not signal_accessible:
            raise PermissionDenied()

        # return an HTTP 404 if we ask for a child signal's children.
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

    @extend_schema(responses={HTTP_200_OK: EmailPreviewSerializer},
                   description='Render the email preview before transitioning to a specific status.')
    @action(detail=True, url_path='email/preview', methods=['POST', ], serializer_class=EmailPreviewPostSerializer,
            serializer_detail_class=EmailPreviewPostSerializer, filterset_class=None)
    def email_preview(self, request, *args, **kwargs):
        """
        Render the email preview before transitioning to a specific status.
        Required parameters: status
        Optional parameters: text
        """
        signal = self.get_object()

        post_serializer = self.get_serializer(data=request.data)
        post_serializer.is_valid(raise_exception=True)

        status = post_serializer.validated_data.pop('status', None)
        text = post_serializer.validated_data.pop('text', None)
        email_override = post_serializer.validated_data.pop('email_override', None)

        status_data = {'state': status, 'text': text, 'send_email': True, 'email_override': email_override}
        subject, _, html_message = trigger_mail_action_for_email_preview(signal, status_data)

        context = self.get_serializer_context()
        context.update({'email_preview': {'subject': subject, 'html_message': html_message}})

        serializer = EmailPreviewSerializer(signal, context=context)
        return Response(serializer.data)

    @extend_schema(responses={HTTP_200_OK: None}, description='Download the Signal as a PDF.')
    @action(detail=True, url_path='pdf', methods=['GET'], url_name='pdf-download')
    def pdf(self, request, *args, **kwargs):
        signal = self.get_object()
        user = request.user

        pdf = PDFSummaryService.get_pdf(signal, user)
        pdf_filename = f'{signal.get_id_display()}.pdf'
        return HttpResponse(pdf, content_type='application/pdf', headers={
            'Content-Disposition': f'attachment;filename="{pdf_filename}"'
        })

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, (list, )):
            serializer = self.get_serializer(data=request.data, many=True)
        else:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)
