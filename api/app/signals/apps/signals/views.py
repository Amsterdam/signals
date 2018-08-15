import logging
import re

from datapunt_api.rest import DatapuntViewSetWritable
from django.conf import settings
from django.http import JsonResponse
from django_filters.rest_framework import (DjangoFilterBackend)
from rest_framework import mixins, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.status import HTTP_202_ACCEPTED
from rest_framework.views import APIView

from signals.apps.signals.filters import (
    LocationFilter,
    SignalFilter,
    StatusFilter)
from signals.apps.signals.models import (
    Category,
    Location,
    Signal,
    Status)
from signals.apps.signals.permissions import (
    CategoryPermission,
    LocationPermission,
    StatusPermission)
from signals.apps.signals.serializers import (
    CategorySerializer,
    LocationSerializer,
    SignalAuthSerializer,
    SignalCreateSerializer,
    SignalUnauthenticatedSerializer,
    SignalUpdateImageSerializer,
    StatusSerializer)
from signals.auth.backend import JWTAuthBackend
from signals.throttling import NoUserRateThrottle

LOGGER = logging.getLogger()


class AuthViewSet:
    http_method_names = ['get', 'post', 'head', 'options', 'trace']
    authentication_classes = (JWTAuthBackend,)


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


class SignalView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """View of Signals for public access.

    Only used to create the signal with POST

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
    http_method_names = ['get', 'post', 'head', 'options', 'trace']

    if not re.search('acc', settings.DATAPUNT_API_URL):
        throttle_classes = (NoUserRateThrottle,)

    serializer_detail_class = SignalCreateSerializer
    serializer_class = SignalCreateSerializer
    pagination_class = None
    lookup_field = 'signal_id'

    def list(self, request, *args, **kwargs):
        return Response({})

    def retrieve(self, request, signal_id=None, **kwargs):
        queryset = Signal.objects.all()
        signal = get_object_or_404(queryset, signal_id=signal_id)
        serializer = SignalUnauthenticatedSerializer(signal, context={'request': request})
        return Response(serializer.data)


class SignalAuthView(AuthViewSet, DatapuntViewSetWritable):
    """View of Signals with reporter information

    !! still in development !!

    only for AUTHENTICATED users
    ============================

    """
    queryset = (
        Signal.objects.all()
        .order_by("created_at")
        .select_related('status')
        .select_related('location')
        .select_related('category')
        .select_related('reporter')
        .order_by('-id')
    )
    serializer_detail_class = SignalAuthSerializer
    serializer_class = SignalAuthSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = SignalFilter


class LocationAuthView(AuthViewSet, DatapuntViewSetWritable):
    permission_classes = (LocationPermission,)
    queryset = (
        Location.objects.all()
        .order_by("created_at")
        .prefetch_related('signal')
    )

    serializer_detail_class = LocationSerializer
    serializer_class = LocationSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = LocationFilter


class StatusAuthView(AuthViewSet, DatapuntViewSetWritable):
    """View of Status Changes"""
    permission_classes = (StatusPermission,)
    queryset = (
        Status.objects.all()
        .order_by("created_at")
    )
    serializer_detail_class = StatusSerializer
    serializer_class = StatusSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = StatusFilter


class CategoryAuthView(AuthViewSet, DatapuntViewSetWritable):
    """View of Types.
    """
    permission_classes = (CategoryPermission,)
    queryset = (
        Category.objects.all()
        .order_by("id").prefetch_related("signal")
    )
    serializer_detail_class = CategorySerializer
    serializer_class = CategorySerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ['main', 'sub']


class LocationUserView(AuthViewSet, APIView):
    """
    Handle information about user me
    """
    def get(self, request):
        data = {}
        user = request.user
        if user:
            data['username'] = user.username
            data['email'] = user.email
            data['is_staff'] = user.is_staff is True
            data['is_superuser'] = user.is_superuser is True
            groups = []
            departments = []
            for g in request.user.groups.all():
                match = re.match(r"^dep_(\w+)$", g.name)
                if match:
                    departments.append(match.group(1))
                else:
                    groups.append(g.name)
            data['groups'] = groups
            data['departments'] = departments
        return JsonResponse(data)
