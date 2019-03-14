import json
import os
from unittest import mock

from django.conf import settings
from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework import serializers
from rest_framework.test import APITestCase

from signals.apps.signals.models import Location
from signals.apps.signals.v0.fields import CategoryLinksField
from signals.apps.signals.v0.serializers import (
    CategoryHALSerializer,
    LocationHALSerializer,
    NearAmsterdamValidatorMixin
)
from tests.apps.signals.factories import SignalFactory
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
        self.assertEqual(correct, v.validate_geometrie(correct))

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
    """
    Test that the user is serialized and deserialized.

    Note: user is added to created_by field as created_by.
    """

    def setUp(self):
        self.signal = SignalFactory.create()
        self.user = UserFactory.create()

        self.location = self.signal.location
        self.location.created_by = self.user.username
        self.location.save()

    def test_user_is_serialized(self):
        serializer = LocationHALSerializer(instance=self.location)
        self.assertIn('created_by', serializer.data)
        self.assertEqual(serializer.data['created_by'], self.user.username)

    def test_user_is_deserialized(self):
        _signal_id = self.signal.id

        request = mock.Mock()
        request.user = self.user

        data = {
            '_signal': _signal_id,
            'stadsdeel': 'A',
            'buurt_code': 'A04i',
            'address': {
                'openbare_ruimte': 'Amstel',
                'huisnummer': 1,
                'huisletter': '',
                'huisnummer_toevoeging': '',
                'postcode': '1011PN',
                'woonplaats': 'Amsterdam',
            },
            'geometrie': {
                'type': 'Point',
                'coordinates': [4.90022563, 52.36768424]
            }
        }

        serializer = LocationHALSerializer(
            data=data, context={'request': request})
        serializer.is_valid()
        location = serializer.save()

        self.assertIsInstance(location, Location)
        self.assertEqual(location.created_by, self.user.username)


class TestCategoryHALSerializer(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create()
        self.user = UserFactory.create()

        self.category_assignment = self.signal.category_assignment
        self.category_assignment.created_by = self.user.username
        self.category_assignment.save()

    def test_user_is_serialized(self):
        class PatchedCategoryLinksField(CategoryLinksField):
            def to_representation(self, value):
                return {'self': {'href': '/link/to/nowhere'}}

        class PatchedSerializer(CategoryHALSerializer):
            serializer_url_field = PatchedCategoryLinksField

        serializer = PatchedSerializer(
            instance=self.category_assignment)
        self.assertIn('created_by', serializer.data)
        self.assertEqual(serializer.data['created_by'], self.user.username)
