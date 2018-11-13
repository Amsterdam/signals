import logging
import re

from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.status import HTTP_202_ACCEPTED
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.signals.filters import (
    FieldMappingOrderingFilter,
    LocationFilter,
    SignalFilter,
    StatusFilter
)
from signals.apps.signals.models import (
    CategoryAssignment,
    History,
    Location,
    MainCategory,
    Note,
    Priority,
    Signal,
    Status,
    SubCategory
)
from signals.apps.signals.permissions import (
    CategoryPermission,
    LocationPermission,
    NotePermission,
    PriorityPermission,
    StatusPermission
)
from signals.apps.signals.serializers import (
    CategoryHALSerializer,
    HistoryHalSerializer,
    LocationHALSerializer,
    MainCategoryHALSerializer,
    NoteHALSerializer,
    PriorityHALSerializer,
    PrivateSignalSerializer,
    SignalAuthHALSerializer,
    SignalCreateSerializer,
    SignalStatusOnlyHALSerializer,
    SignalUpdateImageSerializer,
    StatusHALSerializer,
    SubCategoryHALSerializer
)
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
        'sub_category': 'category_assignment__sub_category__slug',
        'main_category': 'category_assignment__sub_category__main_category__slug',
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
    permission_classes = (LocationPermission, )
    queryset = Location.objects.all().order_by('created_at').prefetch_related('signal')
    serializer_detail_class = LocationHALSerializer
    serializer_class = LocationHALSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = LocationFilter


class StatusAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (StatusPermission, )
    queryset = Status.objects.all().order_by('created_at')
    serializer_detail_class = StatusHALSerializer
    serializer_class = StatusHALSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = StatusFilter


class CategoryAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (CategoryPermission, )
    queryset = CategoryAssignment.objects.all().order_by('id').prefetch_related('signal')
    serializer_detail_class = CategoryHALSerializer
    serializer_class = CategoryHALSerializer
    filter_backends = (DjangoFilterBackend, )


class PriorityAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (PriorityPermission, )
    queryset = Priority.objects.all().order_by('id').prefetch_related('signal')
    serializer_detail_class = PriorityHALSerializer
    serializer_class = PriorityHALSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_fields = ['priority', ]


class NoteAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteHALSerializer
    serializer_detail_class = NoteHALSerializer
    pagination_class = HALPagination
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (NotePermission, )
    filter_backends = (DjangoFilterBackend, )
    filter_fields = ('_signal__id', )


class HistoryAuthViewSet(DatapuntViewSet):
    queryset = History.objects.all()
    serializer_class = HistoryHalSerializer
    serializer_detail_class = HistoryHalSerializer
    pagination_class = HALPagination
    authentication_classes = (JWTAuthBackend, )
    filter_backends = (DjangoFilterBackend, )
    filter_fields = ('_signal__id', )


# -- Views that are used exclusively by the V1 API --

class MainCategoryViewSet(DatapuntViewSet):
    queryset = MainCategory.objects.all()
    serializer_detail_class = MainCategoryHALSerializer
    serializer_class = MainCategoryHALSerializer
    lookup_field = 'slug'


class SubCategoryViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategoryHALSerializer
    pagination_class = HALPagination

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset,
                                main_category__slug=self.kwargs['slug'],
                                slug=self.kwargs['sub_slug'])
        self.check_object_permissions(self.request, obj)
        return obj


class PrivateSignalViewSet(DatapuntViewSet):
    """Viewset for `Signal` objects in V1 private API"""
    queryset = Signal.objects.all()
    serializer_class = PrivateSignalSerializer
    serializer_detail_class = PrivateSignalSerializer
    pagination_class = HALPagination
    authentication_classes = (JWTAuthBackend, )
    filter_backends = (DjangoFilterBackend, )

    @action(detail=True)  # default GET gets routed here
    def history(self, request, pk=None):
        history_entries = History.objects.filter(_signal__id=pk)
        serializer = HistoryHalSerializer(history_entries, many=True)

        return Response(serializer.data)
