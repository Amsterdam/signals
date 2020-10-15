import random

import factory
from django.contrib.gis.geos import MultiPolygon, Polygon

from signals.apps.signals.models import Area, AreaType

# Amsterdam.
BBOX = [4.58565, 52.03560, 5.31360, 52.48769]


def get_random_bbox(bbox=BBOX, n_lon_subdiv=10, n_lat_subdiv=10):
    # Assumes we are away from the antimeridian (i.e. max_lat > min_lat).
    min_lon, min_lat, max_lon, max_lat = bbox
    extent_lon = max_lon - min_lon
    extent_lat = max_lat - min_lat

    ilon = random.randrange(n_lon_subdiv)
    ilat = random.randrange(n_lat_subdiv)

    return Polygon.from_bbox((
        min_lon + (extent_lon / n_lon_subdiv) * ilon,
        min_lat + (extent_lat / n_lat_subdiv) * ilat,
        min_lon + (extent_lon / n_lon_subdiv) * (ilon + 1),
        min_lat + (extent_lat / n_lat_subdiv) * (ilat + 1),
    ))


class AreaTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = AreaType

    name = factory.Sequence(lambda n: f'Gebied type {n}')
    code = factory.Sequence(lambda n: f'gebied-type-code-{n}')
    description = factory.Sequence(lambda n: f'Omschrijving bij gebied type {n}')


class AreaFactory(factory.DjangoModelFactory):
    class Meta:
        model = Area

    name = factory.Sequence(lambda n: f'Gebied type {n}')
    code = factory.Sequence(lambda n: f'gebied-type-code-{n}')
    _type = factory.SubFactory(AreaTypeFactory)
    geometry = MultiPolygon([get_random_bbox()])
