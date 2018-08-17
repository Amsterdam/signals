import json
import os

from django.conf import settings
from django.test import TestCase
from rest_framework.test import APITestCase
from django.core.exceptions import ValidationError


from signals.apps.signals.serializers import NearAmsterdamValidatorMixin
from django.contrib.gis.geos import Point


class NearAmsterdamValidatorMixin(TestCase):
    def test_validate_geometrie(self):
        # note this test bypasses the API
        in_amsterdam = (4.898466, 52.361585)

        correct = Point(in_amsterdam)
        wrong = Point(tuple(reversed(in_amsterdam)))

        # check that valid data is returned, and wrpng data rejected
        validator = NearAmsterdamValidatorMixin()
        self.assertEquals(correct, validator.validate_geometrie(correct))

        with self.assertRaises(ValidationError):
            validator.validate_geometrie(wrong)


class TestLocationSerializer(APITestCase):
    fixture_files = {
        "post_signal": "signal_post.json",
        "post_status": "status_auth_post.json",
        "post_category": "category_auth_post.json",
        "post_location": "location_auth_post.json",
    }

    def _get_fixture(self, name):

        filename = self.fixture_files[name]
        path = os.path.join(
            settings.BASE_DIR,
            'signals',
            'apps',
            'signals',
            'fixtures',
            filename
        )

        with open(path) as fixture_file:
            postjson = json.loads(fixture_file.read())

        return postjson

    def test_wrong_side_of_planet(self):
        pass
#        url = '/signals/auth/location/'
#        
#        payload = self._get_fixture('post_signal')['location']
#        payload['geometrie']['coordinates'] = (4.898466, 52.361585)
#
#        response = self.client.post(url, payload, format='json')
#        self.assertEquals(response.status_code, 201)
    


