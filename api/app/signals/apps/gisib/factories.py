# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import copy

from django.contrib.gis.geos import Point
from factory import LazyAttribute, LazyFunction
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyFloat
from faker import Faker

from signals.apps.gisib.models import GISIBFeature

fake = Faker()

# Amsterdam.
BBOX = [4.58565, 52.03560, 5.31360, 52.48769]


def get_geometry():
    lon = FuzzyFloat(BBOX[0], BBOX[2]).fuzz()
    lat = FuzzyFloat(BBOX[1], BBOX[3]).fuzz()
    return Point(float(lon), float(lat), srid=4326)


def get_gisib_feature(obj):
    """
    Simplified GISIB feature
    """
    geometry = copy.copy(obj.geometry)
    geometry.transform(ct=28992)

    return {
        'type': 'Feature',
        'geometry': {
            'crs': {
                'type': 'name',
                'properties': {
                    'name': 'EPSG:28992'
                }
            },
            'type': 'Point',
            'coordinates': list(geometry.coords)
        },
        'properties': {
            'Id': obj.gisib_id,
            'Soortnaam': {
                'Id': 123456,
                'Url': 'https://amsterdam-test.gisib.nl/api/api/Collections/Soortnaam/items/123456',
                'GUID': '{EC32D5B8-0B0F-4458-930D-C49A6D04695C}',
                'Description': 'Quercus robur'
            },
            'Objecttype': {
                'Id': 654321,
                'Url': 'https://amsterdam-test.gisib.nl/api/api/Collections/Objecttype/items/654321',
                'GUID': '{635136A6-334C-4C9A-B0AD-F69C0CDB52B7}',
                'Description': 'Boom'
            }
        }
    }


class GISIBFeatureFactory(DjangoModelFactory):
    gisib_id = LazyFunction(fake.random_int)
    geometry = get_geometry()
    properties = {
        'object': {
            'type': 'Boom',
            'latin': 'Quercus robur'
        }
    }
    raw_feature = LazyAttribute(lambda o: get_gisib_feature(o))

    class Meta:
        model = GISIBFeature
        django_get_or_create = ('gisib_id',)
