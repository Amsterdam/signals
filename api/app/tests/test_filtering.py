import unittest

from django.contrib.gis.geos import Point
from django.utils.http import urlencode
from rest_framework.test import APITestCase

from tests.factories import SignalFactory
from tests.apps.users.factories import SuperUserFacotry

IN_AMSTERDAM = (4.898466, 52.361585)
N_RECORDS = 10

SIGNAL_ENDPOINT = '/signals/auth/signal/'
STATUS_ENDPOINT = '/signals/auth/status/'
LOCATION_ENDPOINT = '/signals/auth/location/'


class FilterTestDataBase(APITestCase):

    def setUp(self):
        signals = [SignalFactory.create() for i in range(N_RECORDS)]

        # Change the coordinates, to be increasing in both longitude and latitude
        self.dlon = 1e-3  # single increment in longitude
        self.dlat = 1e-3  # single increment in latitude

        for i, signal in enumerate(signals):
            new_point = Point(IN_AMSTERDAM[0] + i * self.dlon,
                              IN_AMSTERDAM[1] + i * self.dlat)
            signal.location.geometrie = new_point
            signal.location.save()

        # Forcing authentication
        superuser = SuperUserFacotry.create()
        self.client.force_authenticate(user=superuser)

    def _get_response(self, endpoint, querystring):
        return self.client.get(f'{endpoint}?{urlencode(querystring)}')


class TestBboxFilter(FilterTestDataBase):

    def test_match_nothing(self):
        # Determine boundingbox that contains no Signals (see setUp).
        min_lon = IN_AMSTERDAM[0] - 0.5 * self.dlon
        max_lon = IN_AMSTERDAM[0] + 0.5 * self.dlon

        min_lat = IN_AMSTERDAM[1] + (N_RECORDS - 0.5) * self.dlat
        max_lat = IN_AMSTERDAM[1] + (N_RECORDS + 0.5) * self.dlat

        response = self._get_response(
            LOCATION_ENDPOINT, {'in_bbox': f'{min_lon},{min_lat},{max_lon},{max_lat}'})

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.json()['count'], 0)

    def test_match_everything(self):
        # Determine boundingbox that contains all Signals (see setUp).
        min_lon = IN_AMSTERDAM[0] - 0.5 * self.dlon
        max_lon = IN_AMSTERDAM[0] + (N_RECORDS + 0.5) * self.dlon

        min_lat = IN_AMSTERDAM[1] - 0.5 * self.dlat
        max_lat = IN_AMSTERDAM[1] + (N_RECORDS + 0.5) * self.dlat

        response = self._get_response(
            LOCATION_ENDPOINT, {'in_bbox': f'{min_lon},{min_lat},{max_lon},{max_lat}'})

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.json()['count'], N_RECORDS)

    def test_match_one(self):
        # Determine boundingbox that contains one single Signal (see setUp).
        min_lon = IN_AMSTERDAM[0] - 0.5 * self.dlon
        max_lon = IN_AMSTERDAM[0] + 0.5 * self.dlon

        min_lat = IN_AMSTERDAM[1] - 0.5 * self.dlat
        max_lat = IN_AMSTERDAM[1] + 0.5 * self.dlat

        response = self._get_response(
            LOCATION_ENDPOINT, {'in_bbox': f'{min_lon},{min_lat},{max_lon},{max_lat}'})

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.json()['count'], 1)

    def test_filter_signal_via_location(self):
        # Determine boundingbox that contains one single Signal (see setUp).
        min_lon = IN_AMSTERDAM[0] - 0.5 * self.dlon
        max_lon = IN_AMSTERDAM[0] + 0.5 * self.dlon

        min_lat = IN_AMSTERDAM[1] - 0.5 * self.dlat
        max_lat = IN_AMSTERDAM[1] + 0.5 * self.dlat

        response = self._get_response(
            SIGNAL_ENDPOINT, {'in_bbox': f'{min_lon},{min_lat},{max_lon},{max_lat}'})

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.json()['count'], 1)

    def test_filter_status_via_location(self):
        # Determine boundingbox that contains one single Status (see setUp).
        min_lon = IN_AMSTERDAM[0] - 0.5 * self.dlon
        max_lon = IN_AMSTERDAM[0] + 0.5 * self.dlon

        min_lat = IN_AMSTERDAM[1] - 0.5 * self.dlat
        max_lat = IN_AMSTERDAM[1] + 0.5 * self.dlat

        response = self._get_response(
            STATUS_ENDPOINT, {'in_bbox': f'{min_lon},{min_lat},{max_lon},{max_lat}'})

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.json()['count'], 1)


class TestLocatieFilter(FilterTestDataBase):

    def test_match_no_instance(self):
        lon = IN_AMSTERDAM[0]
        lat = IN_AMSTERDAM[1] + N_RECORDS * self.dlat

        for endpoint in [LOCATION_ENDPOINT, STATUS_ENDPOINT]:
            response = self._get_response(
                endpoint, {'location': f'{lon},{lat},1'})

            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.json()['count'], 0)

    def test_match_one_instance(self):
        lon, lat = IN_AMSTERDAM

        for endpoint in [LOCATION_ENDPOINT, STATUS_ENDPOINT]:
            response = self._get_response(
                endpoint, {'location': f'{lon},{lat},1'})

            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.json()['count'], 1)

    def test_match_all_instances(self):
        lon, lat = IN_AMSTERDAM

        for endpoint in [LOCATION_ENDPOINT, STATUS_ENDPOINT]:
            response = self._get_response(
                endpoint, {'location': f'{lon},{lat},100000'})

            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.json()['count'], N_RECORDS)

    @unittest.expectedFailure
    def test_signal_filter(self):
        lon, lat = IN_AMSTERDAM

        # Filtering signals by location is not implemented, but probably should,
        # hence this test.
        response = self._get_response(SIGNAL_ENDPOINT, {'location': f'{lon},{lat},1'})

        self.assertEquals(response.status_code, 200)
        # will have N_RECORDS signals because the filter is not yet implemented
        self.assertEquals(response.json()['count'], 1)
