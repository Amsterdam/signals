import json
import os

from django.conf import settings
from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework import serializers
from rest_framework.test import APITestCase

from signals.apps.signals.serializers import (
    LocationHALSerializer,
    NearAmsterdamValidatorMixin,
)
from tests.apps.signals.factories import SignalFactory
from tests.apps.signals.valid_locations import STADHUIS
from tests.apps.users.factories import UserFactory

IN_AMSTERDAM = (4.898466, 52.361585)
OUTSIDE_AMSTERDAM = tuple(reversed(IN_AMSTERDAM))


class TestNearAmsterdamValidatorMixin(TestCase):
    def test_validate_geometrie(self):
        # note this test bypasses the API
        correct = Point(IN_AMSTERDAM)
        wrong = Point(OUTSIDE_AMSTERDAM)

        # check that valid data is returned, and wrong data rejected
        v = NearAmsterdamValidatorMixin()
        self.assertEquals(correct, v.validate_geometrie(correct))

        with self.assertRaises(serializers.ValidationError):
            v.validate_geometrie(wrong)

# TODO: move to endpoint tests (which these are)
class TestLocationSerializer(APITestCase):
    fixtures = ['categories.json', ]

    def _get_fixture(self):
        path = os.path.join(
            settings.BASE_DIR,
            'apps',
            'signals',
            'fixtures',
            'signal_post.json'
        )

        with open(path) as fixture_file:
            postjson = json.loads(fixture_file.read())

        return postjson

    def test_swapped_lon_lat(self):
        """Post een compleet signaal."""
        url = '/signals/signal/'
        payload = self._get_fixture()
        payload['location']['geometrie']['coordinates'] = OUTSIDE_AMSTERDAM

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_correct_lon_lat(self):
        url = '/signals/signal/'
        payload = self._get_fixture()
        payload['location']['geometrie']['coordinates'] = IN_AMSTERDAM

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 201)


class TestLocationSerializerNew(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create()
        self.user = UserFactory.create()

        self.location = self.signal.location
        self.location.created_by = self.user.username
        self.location.save()

    def test_user_is_serialized(self):
        # Note deserialization is tested via API test cases
        serializer = LocationHALSerializer(instance=self.location)
        self.assertIn('created_by', serializer.data)
        self.assertEqual(serializer.data['created_by'], self.user.username)