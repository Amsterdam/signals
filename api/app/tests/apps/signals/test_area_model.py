import random
# from tests.apps.signals import factories

from django.test import TestCase
from signals.apps.signals.models import Area, AreaType, AreaHistory
from django.contrib.gis.geos import MultiPolygon, Point, Polygon


# TODO: Temporary, will be refactored when approach is deemed sound.

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


class AreaTest(TestCase):
    def setUp(self):
        self.area_type_data = {
            'name': 'Stadsdeel',
            'code': 'stadsdeel',
            'description': 'Stadsdeel volgens de SIA Amsterdam definitie.'
        }
        self.area_type = AreaType.objects.create(**self.area_type_data)
        self.area_data = {
            'name': 'Amsterdams Bos',
            'code': 'amsterdams-bos',
            '_type': self.area_type,
            'geometry': MultiPolygon([get_random_bbox()])
        }
        self.area = Area.actions.create_initial(
            None, **self.area_data
        )

    def test_create(self):
        self.assertIsInstance(self.area, Area)
        self.assertEqual(Area.objects.count(), 1)
        self.assertEqual(AreaHistory.objects.count(), 1)

    def test_update(self):
        new_name = 'Triviale naamswijziging.'
        updated_data = {'name': new_name}
        area = Area.actions.update(None, self.area.pk, **updated_data)

        self.assertEqual(area.name, new_name)  # FIX ME

        # Check that we have 2 history entries, the latest with the new name
        self.assertEqual(AreaHistory.objects.count(), 2)
        self.assertEqual(AreaHistory.objects.last().name, new_name)
        self.assertEqual(AreaHistory.objects.first().name, self.area_data['name'])
