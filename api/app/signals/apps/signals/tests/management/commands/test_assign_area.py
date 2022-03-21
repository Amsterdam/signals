# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from io import StringIO

from django.contrib.gis.geos import MultiPolygon, Polygon, Point
from django.core.management import call_command

from signals.apps.signals.factories import AreaFactory, AreaTypeFactory, SignalFactory

# Fake rectangular Amsterdam:
BBOX = [4.58565, 52.03560, 5.31360, 52.48769]


class TestAssignAreas():
    def setUp(self):
        # Create two areas, and one areatype
        # create 3 signals, 1 for area A, 1 for area B and one outside
        self.area_type_district = AreaTypeFactory.create(code='district', name='district')

        min_lon, min_lat, max_lon, max_lat = BBOX
        extent_lon = max_lon - min_lon
        extent_lat = max_lat - min_lat

        w = Polygon.from_bbox((min_lon, min_lat, min_lon + extent_lon * 0.5, min_lat + extent_lat))
        e = Polygon.from_bbox((min_lon + extent_lon * 0.5, min_lat, min_lon + extent_lon, min_lat + extent_lat))

        AreaFactory.create(name='west', code='west', _type=self.area_type_district, geometry=MultiPolygon([w]))
        AreaFactory.create(name='east', code='east', _type=self.area_type_district, geometry=MultiPolygon([e]))

        center_w = Point((min_lon + 0.25 * extent_lon, min_lat + 0.5 * extent_lat))
        center_e = Point((min_lon + 0.75 * extent_lon, min_lat + 0.5 * extent_lat))
        to_north = Point((min_lon + 0.5 * extent_lon, min_lat + 2 * extent_lat))

        self.signal_west = SignalFactory.create(location__geometry=center_w,
                                                location__area_type_code=None,
                                                location__area_type=None,
                                                location__area_name=None)
        self.signal_east = SignalFactory.create(location__geometry=center_e,
                                                location__area_type_code=None,
                                                location__area_type=None,
                                                location__area_name=None)
        self.signal_north = SignalFactory.create(location__geometry=to_north,
                                                 location__area_type_code=None,
                                                 location__area_type=None,
                                                 location__area_name=None)

    def test_assign_area(self):
        buffer = StringIO()
        call_command('assign_area', '--area_type_code=district', stdout=buffer)

        output = buffer.getvalue()
        self.assertIn('Updated area assignment for 2 Signals.', output)
        self.assertIn('There are still 1 Signals without a matching area.', output)

        self.assertEqual(self.signal_west.location.area_type_code, 'district')
        self.assertEqual(self.signal_west.location.area_code, 'west')
        self.assertEqual(self.signal_west.location.area_name, 'west')

        self.assertEqual(self.signal_east.location.area_type_code, 'district')
        self.assertEqual(self.signal_east.location.area_code, 'east')
        self.assertEqual(self.signal_east.location.area_name, 'east')

        self.assertEqual(self.signal_north.location.area_type_code, None)
        self.assertEqual(self.signal_north.location.area_code, None)
        self.assertEqual(self.signal_north.location.area_name, None)
