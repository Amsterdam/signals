from django.test import TestCase

from signals.apps.signals.models import Area, AreaType
from tests.apps.signals import factories


class AreaTest(TestCase):
    def setUp(self):
        self.area = factories.AreaFactory()
        self.area_type = self.area._type

    def test_create(self):
        self.assertEqual(Area.objects.count(), 1)
        self.assertEqual(AreaType.objects.count(), 1)
