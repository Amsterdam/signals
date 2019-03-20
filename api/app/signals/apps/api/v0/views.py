"""
Views that are used exclusively by the V0 API
"""

import logging
import re

from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.status import HTTP_202_ACCEPTED
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.api.generics.filters import (
    FieldMappingOrderingFilter,
    LocationFilter,
    SignalFilter,
    StatusFilter
)
from signals.apps.api.generics.permissions import (
    CategoryPermission,
    LocationPermission,
    NotePermission,
    PriorityPermission,
    SIAAllCategoriesPermission,
    StatusPermission
)
from signals.apps.api.v0.serializers import (
    CategoryHALSerializer,
    LocationHALSerializer,
    NoteHALSerializer,
    PriorityHALSerializer,
    SignalAuthHALSerializer,
    SignalCreateSerializer,
    SignalStatusOnlyHALSerializer,
    SignalUpdateImageSerializer,
    StatusHALSerializer
)
from signals.apps.signals.models import CategoryAssignment, Location, Note, Priority, Signal, Status
from signals.auth.backend import JWTAuthBackend
from signals.throttling import NoUserRateThrottle

logger = logging.getLogger()


# TODO SIG-520 this should be a `action` on the SignalView (set).
class SignalImageUpdateView(viewsets.GenericViewSet):
    """
    Add or update image of newly submitted signals
    """
    serializer_detail_class = SignalUpdateImageSerializer
    serializer_class = SignalUpdateImageSerializer
    pagination_class = None
    queryset = Signal.objects.all()

    def list(self, request, *args, **kwargs):
        return Response({})

    def update(self, request, *args, **kwargs):
        return Response({})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({}, status=HTTP_202_ACCEPTED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}


class SignalViewSet(mixins.CreateModelMixin,
                    DetailSerializerMixin,
                    mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
    """Public endpoint `signals`.

    valid geometrie points are:

        { "type": "Point", "coordinates": [ 4.893697 ,  52.372840 ] }

    or 'POINT (4.893697  52.372840)'

    valid address:
    {
        "openbare_ruimte": "Dam",
        "huisnummer": "1",
        "huisletter": "A",
        "huisnummer_toevoeging": "1",
        "postcode": "1012JS",
        "woonplaats": "Amsterdam"
    }
    """
    if not re.search('acc', settings.DATAPUNT_API_URL):
        throttle_classes = (NoUserRateThrottle,)

    queryset = Signal.objects.all()
    serializer_detail_class = SignalStatusOnlyHALSerializer
    serializer_class = SignalCreateSerializer
    pagination_class = None
    lookup_field = 'signal_id'


class SignalAuthViewSet(DatapuntViewSet):
    authentication_classes = (JWTAuthBackend, )
    queryset = Signal.objects.all()
    serializer_detail_class = SignalAuthHALSerializer
    serializer_class = SignalAuthHALSerializer
    filter_backends = (DjangoFilterBackend, FieldMappingOrderingFilter, )
    filter_class = SignalFilter
    permission_classes = (SIAAllCategoriesPermission,)
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
    ordering = ('-created_at', )

    def get_queryset(self):
        queryset = (
            super().
            get_queryset()
            .select_related('status')
            .select_related('location')
            .select_related('category_assignment')
            .select_related('reporter')
        )
        return queryset


class LocationAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (LocationPermission, SIAAllCategoriesPermission,)
    queryset = Location.objects.all().order_by('created_at').prefetch_related('signal')
    serializer_detail_class = LocationHALSerializer
    serializer_class = LocationHALSerializer
    filter_backends = (DjangoFilterBackend, )
    filterset_class = LocationFilter


class StatusAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (StatusPermission, SIAAllCategoriesPermission,)
    queryset = Status.objects.all().order_by('created_at')
    serializer_detail_class = StatusHALSerializer
    serializer_class = StatusHALSerializer
    filter_backends = (DjangoFilterBackend, )
    filterset_class = StatusFilter


class CategoryAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (CategoryPermission, SIAAllCategoriesPermission,)
    queryset = CategoryAssignment.objects.all().order_by('id').prefetch_related('signal')
    serializer_detail_class = CategoryHALSerializer
    serializer_class = CategoryHALSerializer
    filter_backends = (DjangoFilterBackend, )


class PriorityAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (PriorityPermission, SIAAllCategoriesPermission,)
    queryset = Priority.objects.all().order_by('id').prefetch_related('signal')
    serializer_detail_class = PriorityHALSerializer
    serializer_class = PriorityHALSerializer
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = ['priority', ]


class NoteAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteHALSerializer
    serializer_detail_class = NoteHALSerializer
    pagination_class = HALPagination
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (NotePermission, SIAAllCategoriesPermission,)
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = ('_signal__id', )
