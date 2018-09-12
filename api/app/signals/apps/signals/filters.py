from datapunt_api import bbox
from django.conf import settings
from django.contrib.gis.geos import Point, Polygon
from django_filters.rest_framework import FilterSet, filters
from rest_framework.serializers import ValidationError

from signals.apps.signals.models import STATUS_OPTIONS, Buurt, Location, Signal, Status, Priority

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


def parse_xyr(value):
    """
    Parse lon,lat,radius from querystring for location filter.

    Note:
    - this is a local workaround for the datapunt_api.bbox.parse_xyr which
      should be fixed.
    """
    try:
        lon, lat, radius = value.split(',')
    except ValueError:
        raise ValidationError(
            'location must be longitude,latitude,radius (in meters)'
        )

    try:
        lon = float(lon)
        lat = float(lat)
        radius = float(radius)
    except ValueError:
        raise(
            'locatie must be x: float, y: float, r: float'
        )

    return lon, lat, radius


def buurt_choices():
    options = Buurt.objects.values_list('vollcode', 'naam')
    return [(c, f'{n} ({c})') for c, n in options]


def status_choices():
    return [(c, f'{n} ({c})') for c, n in STATUS_OPTIONS]


def category_sub_choices():
    # fixme: use the distinct query again but also supply the list to frontend
    # options = Category.objects.values_list("sub").distinct()
    return [(subcat, f'{subcat}') for _, _, subcat, _, _ in settings.ALL_SUB_CATEGORIES]


class SignalFilter(FilterSet):
    id = filters.CharFilter()
    in_bbox = filters.CharFilter(method='in_bbox_filter', label='bbox')
    geo = filters.CharFilter(method="locatie_filter", label='x,y,r')

    location__stadsdeel = filters.MultipleChoiceFilter(choices=STADSDELEN)
    location__buurt_code = filters.MultipleChoiceFilter(choices=buurt_choices)
    location__address_text = filters.CharFilter(lookup_expr='icontains')

    created_at = filters.DateFilter(field_name='created_at', lookup_expr='date')
    created_at__gte = filters.DateFilter(field_name='created_at',
                                         lookup_expr='date__gte')
    created_at__lte = filters.DateFilter(field_name='created_at',
                                         lookup_expr='date__lte')

    updated_at = filters.DateFilter(field_name='updated_at', lookup_expr='date')
    updated_at__gte = filters.DateFilter(field_name='updated_at',
                                         lookup_expr='date__gte')
    updated_at__lte = filters.DateFilter(field_name='updated_at',
                                         lookup_expr='date__lte')

    incident_date_start = filters.DateFilter(field_name='incident_date_start',
                                             lookup_expr='date')
    incident_date_start__gte = filters.DateFilter(field_name='incident_date_start',
                                                  lookup_expr='date__gte')
    incident_date_start__lte = filters.DateFilter(field_name='incident_date_start',
                                                  lookup_expr='date__lte')

    incident_date_end = filters.DateFilter(field_name='incident_date_end',
                                           lookup_expr='date')

    operational_date = filters.DateFilter(field_name='operational_date',
                                          lookup_expr='date')
    expire_date = filters.DateFilter(field_name='expire_date', lookup_expr='date')
    expire_date__gte = filters.DateFilter(field_name='expire_date',
                                          lookup_expr='date__gte')
    expire_date__lte = filters.DateFilter(field_name='expire_date',
                                          lookup_expr='date__lte')

    status__state = filters.MultipleChoiceFilter(choices=status_choices)
    category__sub = filters.MultipleChoiceFilter(choices=category_sub_choices)
    priority__priority = filters.MultipleChoiceFilter(choices=Priority.PRIORITY_CHOICES)

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
            "location__address_text",
            "reporter__email",
            "in_bbox",
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

    def locatie_filter(self, qs, name, value):
        lon, lat, radius = parse_xyr(value)
        point = Point(lon, lat)

        return qs.filter(
            location__geometrie__dwithin=(point, bbox.dist_to_deg(radius, lat)))


class StatusFilter(FilterSet):
    id = filters.CharFilter()
    in_bbox = filters.CharFilter(method='in_bbox_filter', label='bbox')
    location = filters.CharFilter(method="locatie_filter", label='x,y,r')

    stadsdeel = filters.ChoiceFilter(choices=STADSDELEN)
    buurt_code = filters.ChoiceFilter(choices=buurt_choices)

    class Meta(object):
        model = Status
        fields = (
            "id",
            "_signal__id",
            "buurt_code",
            "signal__location__stadsdeel",
            "signal__location__buurt_code",
            "created_at",
            # "operational_date",
            "in_bbox",
            "location",
        )

    def locatie_filter(self, qs, name, value):
        lon, lat, radius = parse_xyr(value)
        point = Point(lon, lat)

        return qs.filter(
            signal__location__geometrie__dwithin=(point, bbox.dist_to_deg(radius, lat)))

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
            "_signal__id",
            "buurt_code",
            "signal__location__stadsdeel",
            "signal__location__buurt_code",
            "created_at",
            "in_bbox",
            "location",
        )

    def locatie_filter(self, qs, name, value):
        lon, lat, radius = parse_xyr(value)
        point = Point(lon, lat)

        return qs.filter(geometrie__dwithin=(point, bbox.dist_to_deg(radius, lat)))

    def in_bbox_filter(self, qs, name, value):
        bbox_values, err = bbox.valid_bbox(value)
        lat1, lon1, lat2, lon2 = bbox_values
        poly_bbox = Polygon.from_bbox((lon1, lat1, lon2, lat2))

        if err:
            raise ValidationError(f"bbox invalid {err}:{bbox_values}")
        return qs.filter(geometrie__bboverlaps=poly_bbox)
