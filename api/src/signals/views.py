from django_filters.rest_framework import FilterSet
from django_filters.rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.serializers import ValidationError
from rest_framework import viewsets, mixins
from django.contrib.gis.geos import Polygon

from datapunt_api.rest import DatapuntViewSet
from datapunt_api.rest import DatapuntViewSetWritable
from datapunt_api import bbox

from signals.models import Signal
from signals.models import Location
from signals.models import Category
from signals.models import Status
from signals.models import Buurt
from signals.serializers import SignalCreateSerializer
from signals.serializers import SignalAuthSerializer
from signals.serializers import LocationSerializer
from signals.serializers import CategorySerializer
from signals.serializers import StatusSerializer


STADSDELEN = (
    ("B", "Westpoort (B)"),
    ("M", "Oost (M)"),
    ("N", "Noord (N)"),
    ("A", "Centrum (A)"),
    ("E", "West (E)"),
    ("F", "Nieuw-West (F)"),
    ("K", "Zuid (K)"),
    ("T", "Zuidoost (T)"),
)


def buurt_choices():
    # noinspection PyUnresolvedReferences
    options = Buurt.objects.values_list('vollcode', 'naam')
    return [(c, '%s (%s)' % (n, c)) for c, n in options]


class SignalFilter(FilterSet):
    id = filters.CharFilter()
    in_bbox = filters.CharFilter(method='in_bbox_filter', label='bbox')
    geo = filters.CharFilter(method="locatie_filter", label='x,y,r')

    location__stadsdeel = filters.ChoiceFilter(choices=STADSDELEN)
    location__buurt_code = filters.ChoiceFilter(choices=buurt_choices)

    extra = filters.CharFilter(method='in_extra', label='extra')

    created_at = filters.DateFilter(name='created_at', lookup_expr='date')
    created_at__gte = filters.DateFilter(name='created_at', lookup_expr='date__gte')
    created_at__lte = filters.DateFilter(name='created_at', lookup_expr='date__lte')

    updated_at = filters.DateFilter(name='updated_at', lookup_expr='date')
    updated_at__gte = filters.DateFilter(name='updated_at', lookup_expr='date__gte')
    updated_at__lte = filters.DateFilter(name='updated_at', lookup_expr='date__lte')

    status_not__state = filters.CharFilter(name='status__state', exclude=True)

    class Meta(object):
        model = Signal
        fields = (
            "id",
            "signal_id",
            "status__state",
            "category__main",
            "category__sub",
            "updated_at",
            "location__buurt_code",
            "location__stadsdeel",
            "reporter__email",
            "in_bbox",
            "extra",
            "geo",
        )

    def in_bbox_filter(self, qs, name, value):
        bbox_values, err = bbox.valid_bbox(value)
        lat1, lon1, lat2, lon2 = bbox_values
        poly_bbox = Polygon.from_bbox((lon1, lat1, lon2, lat2))

        if err:
            raise ValidationError(
                f"bbox invalid {err}:{bbox_values}")
        return qs.filter(
            location__geometrie__bboverlaps=poly_bbox)

    def in_extra(self, qs, name, value):
        """
        Filter in extra json field
        """
        # TODO
        return qs

    def locatie_filter(self, qs, name, value):
        point, radius = bbox.parse_xyr(value)
        return qs.filter(
            location__geometrie__dwithin=(point, radius))


class AuthViewSet:
    def check_permissions(self, request):
        scope = 'SIG/ALL'
        if not request.is_authorized_for(scope):
            self.permission_denied(
                request, message=getattr(scope, 'message', None)
            )
        return super(AuthViewSet, self).check_permissions(request)


class SignalView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """View of Signals for public access.

    Only used to create the signal with POST

    valid geometrie points are:

        { 'type': 'Point', 'coordinates': [ 135.0, 45.0, ], }

    or 'POINT (12.492324113849 41.890307434153)'
    """
    serializer_detail_class = SignalCreateSerializer
    serializer_class = SignalCreateSerializer
    pagination_class = None


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


class StatusFilter(FilterSet):

    id = filters.CharFilter()
    in_bbox = filters.CharFilter(method='in_bbox_filter', label='bbox')
    location = filters.CharFilter(
        method="locatie_filter", label='x,y,r')

    stadsdeel = filters.ChoiceFilter(choices=STADSDELEN)
    buurt_code = filters.ChoiceFilter(choices=buurt_choices)

    class Meta(object):
        model = Status
        fields = (
            "id",
            "signal__id",
            "buurt_code",
            "signal__location__stadsdeel",
            "signal__location__buurt_code",
            "created_at",
            # "operational_date",
            "in_bbox",
            "location",
        )

    def locatie_filter(self, qs, name, value):
        point, radius = bbox.parse_xyr(value)
        return qs.filter(signal__location__geometrie__dwithin=(point, radius))

    def in_bbox_filter(self, qs, name, value):
        bbox_values, err = bbox.valid_bbox(value)
        lat1, lon1, lat2, lon2 = bbox_values
        poly_bbox = Polygon.from_bbox((lon1, lat1, lon2, lat2))

        if err:
            raise ValidationError(f"bbox invalid {err}:{bbox_values}")
        return qs.filter(signal__location__geometrie__bboverlaps=poly_bbox)


class LocationFilter(FilterSet):
    """
    """
    id = filters.CharFilter()
    in_bbox = filters.CharFilter(method='in_bbox_filter', label='bbox')
    location = filters.CharFilter(
        method="locatie_filter", label='x,y,r')

    stadsdeel = filters.ChoiceFilter(choices=STADSDELEN)
    buurt_code = filters.ChoiceFilter(choices=buurt_choices)

    class Meta(object):
        model = Location
        fields = (
            "id",
            "signal",
            "buurt_code",
            "signal__location__stadsdeel",
            "signal__location__buurt_code",
            "created_at",
            "in_bbox",
            "location",
        )

    def locatie_filter(self, qs, name, value):
        point, radius = bbox.parse_xyr(value)
        return qs.filter(geometrie__dwithin=(point, radius))

    def in_bbox_filter(self, qs, name, value):
        bbox_values, err = bbox.valid_bbox(value)
        lat1, lon1, lat2, lon2 = bbox_values
        poly_bbox = Polygon.from_bbox((lon1, lat1, lon2, lat2))

        if err:
            raise ValidationError(f"bbox invalid {err}:{bbox_values}")
        return qs.filter(geometrie__bboverlaps=poly_bbox)


class LocationView(DatapuntViewSet):

    queryset = (
        Location.objects.all()
        .order_by("created_at")
        .prefetch_related('signal')
    )

    serializer_detail_class = LocationSerializer
    serializer_class = LocationSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = LocationFilter


class LocationAuthView(AuthViewSet, DatapuntViewSetWritable):

    queryset = (
        Location.objects.all()
        .order_by("created_at")
        .prefetch_related('signal')
    )

    serializer_detail_class = LocationSerializer
    serializer_class = LocationSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = LocationFilter


class StatusView(DatapuntViewSet):
    """View of Status Changes"""
    queryset = (
        Status.objects.all()
        .order_by("created_at")
        .prefetch_related('signal')
    )
    serializer_detail_class = StatusSerializer
    serializer_class = StatusSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = StatusFilter


class StatusAuthView(AuthViewSet, DatapuntViewSetWritable):
    """View of Status Changes"""
    queryset = (
        Status.objects.all()
        .order_by("created_at")
        .prefetch_related('signal')
    )
    serializer_detail_class = StatusSerializer
    serializer_class = StatusSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = StatusFilter


class CategoryView(DatapuntViewSet):
    """View of Types.
    """
    queryset = (
        Category.objects.all()
        .order_by("id").prefetch_related("signal")
    )
    serializer_detail_class = CategorySerializer
    serializer_class = CategorySerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ['main', 'sub']


class CategoryAuthView(AuthViewSet, DatapuntViewSetWritable):
    """View of Types.
    """
    queryset = (
        Category.objects.all()
        .order_by("id").prefetch_related("signal")
    )
    serializer_detail_class = CategorySerializer
    serializer_class = CategorySerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ['main', 'sub']
