from tests.apps.signals import factories

from django.test import TestCase
from django.contrib.gis.geos import MultiPolygon
from signals.apps.signals.models import Area, AreaProperties, AreaType


class AreaTest(TestCase):
    def setUp(self):
        self.area = factories.AreaFactory.create()
        self.area_type = self.area.type
        self.area_properties = self.area.properties

    def test_create(self):
        _type = AreaType.objects.create(
            name='Stadsdeel',
            code='stadsdeel',
            description='SIA stadsdeel definitie.'
        )
        area = Area.objects.create(
            code='amsterdams-bos',
            type=_type,
        )

        for i in range(10):
            last = AreaProperties.objects.create(
                name='Amsterdams Bos',
                geometry=MultiPolygon(factories.get_random_bbox()),
                created_by='test@example.com',
                area=area
            )

        self.assertIsInstance(self.area, Area)
        self.assertIsInstance(self.area.type, AreaType)
        self.assertIsInstance(self.area.properties.last(), AreaProperties)

        # MODEL MANAGER TRICKS WORK:
        b = Area.objects.get(id=area.id)
        self.assertTrue(hasattr(b, 'updated_at'))
        self.assertTrue(hasattr(b, 'created_at'))
        self.assertNotEqual(b.updated_at, b.created_at)

        # BUT THESE DON'T WORK:
        self.assertTrue(hasattr(self.area, 'updated_at'))
        self.assertTrue(hasattr(self.area, 'created_at'))

    def test_factories(self):
        self.assertIsInstance(self.area, Area)
        self.assertIsInstance(self.area_type, AreaType)

        self.assertIsInstance(self.area_properties.last(), AreaProperties)
