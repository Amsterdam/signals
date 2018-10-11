import logging
import re

from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.status import HTTP_202_ACCEPTED
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.signals.filters import LocationFilter, SignalFilter, StatusFilter
from signals.apps.signals.models import (
    CategoryAssignment,
    Location,
    MainCategory,
    Priority,
    Signal,
    Status,
    SubCategory
)
from signals.apps.signals.permissions import (
    CategoryPermission,
    LocationPermission,
    PriorityPermission,
    StatusPermission
)
from signals.apps.signals.serializers import (
    CategoryHALSerializer,
    LocationHALSerializer,
    MainCategoryHALSerializer,
    PriorityHALSerializer,
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
    queryset = (
        Signal.objects.all()
        .select_related('status')
        .select_related('location')
        .select_related('category_assignment')
        .select_related('reporter'))
    serializer_detail_class = SignalAuthHALSerializer
    serializer_class = SignalAuthHALSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, )
    filter_class = SignalFilter
    ordering_fields = (
        'id',
        'created_at',
        'updated_at',
        'location__stadsdeel',
        'category_assignment__sub_category__slug',
        'category_assignment__sub_category__main_category__slug',
        'status__state',
        'priority__priority',
        'location__address_text',
    )
    ordering = ('-created_at', )


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
