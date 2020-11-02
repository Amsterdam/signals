from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework import serializers

from signals.apps.api.generics.mixins import WithinBoundingBoxValidatorMixin

IN_THE_NETHERLANDS = (4.898466, 52.361585)
OUTSIDE_THE_NETHERLANDS = tuple(reversed(IN_THE_NETHERLANDS))


class TestWithinBoundingBoxValidatorMixin(TestCase):
    def test_validate_geometrie(self):
        # note this test bypasses the API
        correct = Point(IN_THE_NETHERLANDS)
        wrong = Point(OUTSIDE_THE_NETHERLANDS)

        # check that valid data is returned, and wrong data rejected
        v = WithinBoundingBoxValidatorMixin()
        self.assertEqual(correct, v.validate_geometrie(correct))

        with self.assertRaises(serializers.ValidationError):
            v.validate_geometrie(wrong)
