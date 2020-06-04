from django.contrib.gis.geos import MultiPolygon, Polygon
from django.test import TestCase

from signals.apps.dataset.sources.sia_stadsdeel import SIAStadsdeelLoader
from signals.apps.signals.models import Area, AreaType

RD_STADHUIS = [121853, 486780]


class TestLoadSIAStadsdeel(TestCase):
    def setUp(self):
        self.loader = SIAStadsdeelLoader('sia-stadsdeel')
        # "sia-stadsdeel" type Areas are derived from "stadsdeel" type Areas,
        # here we create "stadsdeel" AreaType and provide some Area instances
        # using that type
        stadsdeel_area_type = AreaType.objects.create(
            name='Stadsdeel',
            code='stadsdeel',
            description='Stadsdeel voor tests.'
        )
        cbs_gemeente_type = AreaType.objects.create(
            name='Stadsdeel',
            code='cbs-gemeente-2019',
            description='CBS gemeentegrens voor tests.'
        )

        # We create three city distticts of 10x10 meters located at City Hall to
        # test with. (Code stolen from the Gebieden API tests.)
        x, y = RD_STADHUIS
        width, height = 10, 10
        self.bbox_1 = [x, y, x + width, y + height]
        self.bbox_2 = [x, y + height, x + width, y + 2 * height]
        self.bbox_3 = [x, y + 2 * height, x + width, y + 3 * height]

        zuid_geometry = MultiPolygon([Polygon.from_bbox(self.bbox_1)])
        zuid_geometry.srid = 28992
        zuid_geometry.transform(ct=4326)
        noord_geometry = MultiPolygon([Polygon.from_bbox(self.bbox_2)])
        noord_geometry.srid = 28992
        noord_geometry.transform(ct=4326)
        weesp_geometry = MultiPolygon([Polygon.from_bbox(self.bbox_3)])
        weesp_geometry.srid = 28992
        weesp_geometry.transform(ct=4326)

        Area.objects.create(
            name='Zuid',
            code='SOME_CBS_CODE_1',
            _type=stadsdeel_area_type,
            geometry=zuid_geometry,
        )
        Area.objects.create(
            name='Noord',
            code='SOME_CBS_CODE_2',
            _type=stadsdeel_area_type,
            geometry=noord_geometry,
        )
        Area.objects.create(
            name='Weesp',
            code='SOME_CBS_CODE_3',
            _type=cbs_gemeente_type,
            geometry=weesp_geometry,
        )

        self.assertEqual(Area.objects.count(), 3)
        self.assertEqual(Area.objects.filter(_type__code='stadsdeel').count(), 2)

    def test__load_amsterdamse_bos_geometry(self):
        # Since the method being tested only loads a hard-coded data file,
        # we just call the function and do some basic checks on the output.
        out = self.loader._load_amsterdamse_bos_geometry()
        self.assertIsInstance(out, MultiPolygon)
        self.assertEqual(out.srid, 4326)

    def test_load(self):
        self.assertEqual(Area.objects.count(), 3)
        self.assertEqual(Area.objects.filter(_type__code='stadsdeel').count(), 2)
        self.loader.load()

        # There should be four "sia-stadsdeel" type areas (Amsterdamse bos,
        # zuid, noord and weesp).
        self.assertEqual(Area.objects.filter(_type__code='sia-stadsdeel').count(), 4)

        # Since we know "Het Amsterdamse Bos" does not intersect City Hall:
        zuid = Area.objects.get(name__iexact='zuid', _type__code='stadsdeel')
        sia_zuid = Area.objects.get(name__iexact='zuid', _type__code='sia-stadsdeel')

        self.assertEqual(zuid.geometry, sia_zuid.geometry)
