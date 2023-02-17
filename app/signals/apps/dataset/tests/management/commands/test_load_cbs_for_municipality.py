# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from io import StringIO

from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.management import CommandError, call_command
from django.test import TestCase

from signals.apps.dataset.management.commands.load_cbs_for_municipality import REQUIRED_DATASETS
from signals.apps.signals.factories import AreaFactory, AreaTypeFactory
from signals.apps.signals.models import Area, AreaType

# Fake rectangular Amsterdam:
BBOX = [4.58565, 52.03560, 5.31360, 52.48769]


class TestLoadCBSForMunicipality(TestCase):
    def setUp(self):
        # This setUp stands in for the cbs.py data loading script run for the
        # relevant datasets. Note that REQUIRED_DATASETS must match what's in
        # the CBS dataloader cbs.py.
        self.area_type_code_m = REQUIRED_DATASETS['CBS_MUNICIPAL_BORDERS_DATASET']
        self.area_type_code_w = REQUIRED_DATASETS['CBS_WIJK_DATASET']
        self.area_type_code_b = REQUIRED_DATASETS['CBS_BUURT_DATASET']

        self.area_type_m = AreaTypeFactory.create(code=self.area_type_code_m, name=self.area_type_code_m)
        self.area_type_w = AreaTypeFactory.create(code=self.area_type_code_w, name=self.area_type_code_w)
        self.area_type_b = AreaTypeFactory.create(code=self.area_type_code_b, name=self.area_type_code_b)

        min_lon, min_lat, max_lon, max_lat = BBOX
        extent_lon = max_lon - min_lon
        extent_lat = max_lat - min_lat

        amsterdam_geom = MultiPolygon([Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))])
        self.area_amsterdam = AreaFactory(
            name='Amsterdam', code='GM0363', _type=self.area_type_m, geometry=amsterdam_geom)

        # Area in fake Amsterdam:
        polygon_in = Polygon.from_bbox((
            min_lon + extent_lon * 0.25,
            min_lat + extent_lat * 0.25,
            min_lon + extent_lon * 0.75,
            min_lat + extent_lat * 0.75,
        ))
        # Area in fake Amsterdam:
        polygon_out = Polygon.from_bbox((
            min_lon + extent_lon * 1.25,
            min_lat + extent_lat * 0.25,
            min_lon + extent_lon * 1.75,
            min_lat + extent_lat * 0.75,
        ))

        # Neighborhoods (note these are not valid CBS codes!)
        self.area_in_amsterdam_w = AreaFactory.create(
            name='Wijk in Amsterdam', code='WK036301', _type=self.area_type_w, geometry=MultiPolygon([polygon_in]))
        self.area_in_amsterdam_b = AreaFactory(
            name='Buurt in Amsterdam', code='BU03630101', _type=self.area_type_b, geometry=MultiPolygon(polygon_in))

        self.area_outside_amsterdam_w = AreaFactory(
            name='Wijk buiten Amsterdam', code='WK01', _type=self.area_type_w, geometry=MultiPolygon([polygon_out]))
        self.area_outside_amsterdam_b = AreaFactory(
            name='Buurt buiten', code='BU01234', _type=self.area_type_b, geometry=MultiPolygon([polygon_out]))

    # happy flow
    def test_load_wijk_and_buurt(self):
        self.assertEqual(AreaType.objects.count(), 3)
        self.assertEqual(Area.objects.count(), 5)

        buffer = StringIO()
        call_command('load_cbs_for_municipality', '--municipal_code=GM0363', stdout=buffer)

        output = buffer.getvalue()
        self.assertIn('Done.', output)

        self.assertEqual(AreaType.objects.count(), 5)
        self.assertEqual(Area.objects.count(), 7)

        self.assertEqual(Area.objects.filter(_type__code='gm0363-wijk').count(), 1)  # one "wijk" in Amsterdam
        self.assertEqual(Area.objects.filter(_type__code='gm0363-buurt').count(), 1)  # one "buurt" in Amsterdam

    # unhappy flow
    def test_municipal_code_does_not_exist(self):
        self.assertEqual(AreaType.objects.count(), 3)
        self.assertEqual(Area.objects.count(), 5)

        # Data present, but no valid municipal code is supplied
        with self.assertRaises(CommandError) as cm:
            call_command('load_cbs_for_municipality', '--municipal_code=DOES_NOT_EXIST')
        e = cm.exception
        self.assertIn(str(e), 'Provided municipal code is not present in CBS data, exiting!')

        # Check that we loaded nothing
        self.assertEqual(AreaType.objects.count(), 3)
        self.assertEqual(Area.objects.count(), 5)

    def test_CBS_BUURT_DATASET_area_type_missing(self):
        self.assertEqual(AreaType.objects.count(), 3)
        self.assertEqual(Area.objects.count(), 5)

        # AreaType for CBS buurt data is missing
        AreaType.objects.filter(code=self.area_type_code_b).delete()

        with self.assertRaises(CommandError) as cm:
            call_command('load_cbs_for_municipality', '--municipal_code=GM0363')
        e = cm.exception
        self.assertIn(str(e), 'Required datasets are not available, exiting!')

        # Check that we loaded nothing
        self.assertEqual(AreaType.objects.count(), 2)  # we did delete one AreaType
        self.assertEqual(Area.objects.count(), 3)  # cascading delete removed two Areas

    def test_CBS_BUURT_DATASET_areas_missing(self):
        self.assertEqual(AreaType.objects.count(), 3)
        self.assertEqual(Area.objects.count(), 5)

        # AreaType for CBS buurt data is missing
        Area.objects.filter(_type__code=self.area_type_code_b).delete()

        with self.assertRaises(CommandError) as cm:
            call_command('load_cbs_for_municipality', '--municipal_code=GM0363')
        e = cm.exception
        self.assertIn(str(e), 'Required datasets are not available, exiting!')

        # Check that we loaded nothing
        self.assertEqual(AreaType.objects.count(), 3)
        self.assertEqual(Area.objects.count(), 3)  # we deleted two Areas
