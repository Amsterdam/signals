from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework import serializers

from signals.apps.api.generics.mixins import NearAmsterdamValidatorMixin

IN_AMSTERDAM = (4.898466, 52.361585)
OUTSIDE_AMSTERDAM = tuple(reversed(IN_AMSTERDAM))


class TestNearAmsterdamValidatorMixin(TestCase):
    def test_validate_geometrie(self):
        # note this test bypasses the API
        correct = Point(IN_AMSTERDAM)
        wrong = Point(OUTSIDE_AMSTERDAM)

        # check that valid data is returned, and wrong data rejected
        v = NearAmsterdamValidatorMixin()
        self.assertEqual(correct, v.validate_geometrie(correct))

        with self.assertRaises(serializers.ValidationError):
            v.validate_geometrie(wrong)
