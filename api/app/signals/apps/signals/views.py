import logging
import re

from datapunt_api.rest import DatapuntViewSet
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.status import HTTP_202_ACCEPTED
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.signals.filters import (
    LocationFilter,
    SignalFilter,
    StatusFilter
)
from signals.apps.signals.models import Category, Location, Signal, Status
from signals.apps.signals.permissions import (
    CategoryPermission,
    LocationPermission,
    StatusPermission
)
from signals.apps.signals.serializers import (
    CategorySerializer,
    LocationSerializer,
    SignalAuthSerializer,
    SignalCreateSerializer,
    SignalStatusOnlySerializer,
    SignalUpdateImageSerializer,
    StatusSerializer
)
from signals.auth.backend import JWTAuthBackend
from signals.throttling import NoUserRateThrottle

LOGGER = logging.getLogger()


# TODO SIG-520 this should be a `action` on the SignalView (set).
class SignalImageUpdateView(viewsets.GenericViewSet):
    """
    Add or update image of newly submitted signals
    """
    serializer_detail_class = SignalUpdateImageSerializer
    serializer_class = SignalUpdateImageSerializer
    pagination_class = None

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
    serializer_detail_class = SignalStatusOnlySerializer
    serializer_class = SignalCreateSerializer
    pagination_class = None
    lookup_field = 'signal_id'


class SignalAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    authentication_classes = (JWTAuthBackend, )
    queryset = (
        Signal.objects.all()
        .order_by('created_at')
        .select_related('status')
        .select_related('location')
        .select_related('category')
        .select_related('reporter')
        .order_by('-id')
    )
    serializer_detail_class = SignalAuthSerializer
    serializer_class = SignalAuthSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = SignalFilter


class LocationAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (LocationPermission, )
    queryset = Location.objects.all().order_by('created_at').prefetch_related('signal')
    serializer_detail_class = LocationSerializer
    serializer_class = LocationSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = LocationFilter


class StatusAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (StatusPermission, )
    queryset = Status.objects.all().order_by('created_at')
    serializer_detail_class = StatusSerializer
    serializer_class = StatusSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = StatusFilter


class CategoryAuthViewSet(mixins.CreateModelMixin, DatapuntViewSet):
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (CategoryPermission, )
    queryset = Category.objects.all().order_by('id').prefetch_related('signal')
    serializer_detail_class = CategorySerializer
    serializer_class = CategorySerializer
    filter_backends = (DjangoFilterBackend, )
    filter_fields = ['main', 'sub']
