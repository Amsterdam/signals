import unittest

from django.contrib.gis.geos import Point
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, TestCase
from django.utils.http import urlencode
from rest_framework.mixins import ListModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.test import APITestCase
from rest_framework.viewsets import GenericViewSet

from signals.apps.signals.api_generics.filters import FieldMappingOrderingFilter
from signals.apps.signals.models import MainCategory, Priority, Signal, SubCategory
from signals.apps.signals.v0.serializers import SignalAuthHALSerializer
from tests.apps.signals.factories import SignalFactory
from tests.apps.users.factories import SuperUserFactory

IN_AMSTERDAM = (4.898466, 52.361585)
N_RECORDS = 10

SIGNAL_ENDPOINT = '/signals/auth/signal/'
STATUS_ENDPOINT = '/signals/auth/status/'
LOCATION_ENDPOINT = '/signals/auth/location/'


class TestFilterBase(APITestCase):

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
        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)

    def _get_response(self, endpoint, querystring):
        return self.client.get(f'{endpoint}?{urlencode(querystring)}')


class TestBboxFilter(TestFilterBase):

    def test_match_nothing(self):
        # Determine boundingbox that contains no Signals (see setUp).
        min_lon = IN_AMSTERDAM[0] - 0.5 * self.dlon
        max_lon = IN_AMSTERDAM[0] + 0.5 * self.dlon

        min_lat = IN_AMSTERDAM[1] + (N_RECORDS - 0.5) * self.dlat
        max_lat = IN_AMSTERDAM[1] + (N_RECORDS + 0.5) * self.dlat

        response = self._get_response(
            LOCATION_ENDPOINT, {'in_bbox': f'{min_lon},{min_lat},{max_lon},{max_lat}'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 0)

    def test_match_everything(self):
        # Determine boundingbox that contains all Signals (see setUp).
        min_lon = IN_AMSTERDAM[0] - 0.5 * self.dlon
        max_lon = IN_AMSTERDAM[0] + (N_RECORDS + 0.5) * self.dlon

        min_lat = IN_AMSTERDAM[1] - 0.5 * self.dlat
        max_lat = IN_AMSTERDAM[1] + (N_RECORDS + 0.5) * self.dlat

        response = self._get_response(
            LOCATION_ENDPOINT, {'in_bbox': f'{min_lon},{min_lat},{max_lon},{max_lat}'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], N_RECORDS)

    def test_match_one(self):
        # Determine boundingbox that contains one single Signal (see setUp).
        min_lon = IN_AMSTERDAM[0] - 0.5 * self.dlon
        max_lon = IN_AMSTERDAM[0] + 0.5 * self.dlon

        min_lat = IN_AMSTERDAM[1] - 0.5 * self.dlat
        max_lat = IN_AMSTERDAM[1] + 0.5 * self.dlat

        response = self._get_response(
            LOCATION_ENDPOINT, {'in_bbox': f'{min_lon},{min_lat},{max_lon},{max_lat}'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)

    def test_filter_signal_via_location(self):
        # Determine boundingbox that contains one single Signal (see setUp).
        min_lon = IN_AMSTERDAM[0] - 0.5 * self.dlon
        max_lon = IN_AMSTERDAM[0] + 0.5 * self.dlon

        min_lat = IN_AMSTERDAM[1] - 0.5 * self.dlat
        max_lat = IN_AMSTERDAM[1] + 0.5 * self.dlat

        response = self._get_response(
            SIGNAL_ENDPOINT, {'in_bbox': f'{min_lon},{min_lat},{max_lon},{max_lat}'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)

    def test_filter_status_via_location(self):
        # Determine boundingbox that contains one single Status (see setUp).
        min_lon = IN_AMSTERDAM[0] - 0.5 * self.dlon
        max_lon = IN_AMSTERDAM[0] + 0.5 * self.dlon

        min_lat = IN_AMSTERDAM[1] - 0.5 * self.dlat
        max_lat = IN_AMSTERDAM[1] + 0.5 * self.dlat

        response = self._get_response(
            STATUS_ENDPOINT, {'in_bbox': f'{min_lon},{min_lat},{max_lon},{max_lat}'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)


class TestLocatieFilter(TestFilterBase):

    def test_match_no_instance(self):
        lon = IN_AMSTERDAM[0]
        lat = IN_AMSTERDAM[1] + N_RECORDS * self.dlat

        for endpoint in [LOCATION_ENDPOINT, STATUS_ENDPOINT]:
            response = self._get_response(
                endpoint, {'location': f'{lon},{lat},1'})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['count'], 0)

    def test_match_one_instance(self):
        lon, lat = IN_AMSTERDAM

        for endpoint in [LOCATION_ENDPOINT, STATUS_ENDPOINT]:
            response = self._get_response(
                endpoint, {'location': f'{lon},{lat},1'})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['count'], 1)

    def test_match_all_instances(self):
        lon, lat = IN_AMSTERDAM

        for endpoint in [LOCATION_ENDPOINT, STATUS_ENDPOINT]:
            response = self._get_response(
                endpoint, {'location': f'{lon},{lat},100000'})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['count'], N_RECORDS)

    @unittest.expectedFailure
    def test_signal_filter(self):
        lon, lat = IN_AMSTERDAM

        # Filtering signals by location is not implemented, but probably should,
        # hence this test.
        response = self._get_response(SIGNAL_ENDPOINT, {'location': f'{lon},{lat},1'})

        self.assertEqual(response.status_code, 200)
        # will have N_RECORDS signals because the filter is not yet implemented
        self.assertEqual(response.json()['count'], 1)


class TestPriorityFilter(APITestCase):

    def setUp(self):
        # Forcing authentication
        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)

        SignalFactory.create(id=1)
        SignalFactory.create(id=2)
        SignalFactory.create(id=3, priority__priority=Priority.PRIORITY_HIGH)
        SignalFactory.create(id=4)
        SignalFactory.create(id=5, priority__priority=Priority.PRIORITY_HIGH)

    def test_all(self):
        response = self.client.get(SIGNAL_ENDPOINT)
        json_response = response.json()

        self.assertEqual(Signal.objects.count(), 5)
        self.assertEqual(json_response['count'], 5)

    def test_priority_filter_normal(self):
        querystring = {'priority__priority': Priority.PRIORITY_NORMAL}
        url = f'{SIGNAL_ENDPOINT}?{urlencode(querystring)}'
        response = self.client.get(url)
        json_response = response.json()

        self.assertEqual(json_response['count'], 3)
        self.assertEqual(json_response['results'][2]['id'], 1)
        self.assertEqual(json_response['results'][1]['id'], 2)
        self.assertEqual(json_response['results'][0]['id'], 4)

    def test_priority_filter_high(self):
        querystring = {'priority__priority': Priority.PRIORITY_HIGH}
        url = f'{SIGNAL_ENDPOINT}?{urlencode(querystring)}'
        response = self.client.get(url)
        json_response = response.json()

        self.assertEqual(json_response['count'], 2)
        self.assertEqual(json_response['results'][1]['id'], 3)
        self.assertEqual(json_response['results'][0]['id'], 5)


class TestFieldMappingOrderingFilter(TestCase):

    def setUp(self):
        self.request_factory = RequestFactory()
        self.fake_request = self.request_factory.get('/fake_request')
        self.fake_request_ordering = self.request_factory.get('/fake_request?ordering=created_at')

    def test_with_ordering_querystring(self):
        # Creating an inline ViewSet class.
        class MyViewSet(GenericViewSet, ListModelMixin):
            queryset = Signal.objects.all()
            pagination_class = LimitOffsetPagination
            serializer_class = SignalAuthHALSerializer
            filter_backends = (FieldMappingOrderingFilter, )
            ordering_fields = (
                'created_at',
                'address',
            )
            ordering_field_mappings = {
                'created_at': 'created_at',
                'address': 'address',
            }

        # Creating a fake request to initiate the view.
        view = MyViewSet.as_view({'get': 'list'})
        response = view(self.fake_request_ordering)

        self.assertEqual(response.status_code, 200)

    def test_without_ordering_querystring(self):
        # Creating an inline ViewSet class.
        class MyViewSet(GenericViewSet, ListModelMixin):
            queryset = Signal.objects.all()
            pagination_class = LimitOffsetPagination
            serializer_class = SignalAuthHALSerializer
            filter_backends = (FieldMappingOrderingFilter, )
            ordering_fields = (
                'created_at',
                'address',
            )
            ordering_field_mappings = {
                'created_at': 'created_at',
                'address': 'address',
            }

        # Creating a fake request (without querystring `ordering`) to initiate the view.
        view = MyViewSet.as_view({'get': 'list'})
        response = view(self.fake_request)

        self.assertEqual(response.status_code, 200)

    def test_missing_attribute_ordering_field_mappings(self):
        # Creating an inline ViewSet class.
        class MyViewSet(GenericViewSet, ListModelMixin):
            queryset = Signal.objects.all()
            pagination_class = LimitOffsetPagination
            serializer_class = SignalAuthHALSerializer
            filter_backends = (FieldMappingOrderingFilter, )
            ordering_fields = (
                'created_at',
                'address',
            )

        # Creating a fake request to initiate the view.
        view = MyViewSet.as_view({'get': 'list'})

        with self.assertRaises(ImproperlyConfigured) as exp:
            view(self.fake_request_ordering)
        self.assertEqual(str(exp.exception),
                         ('Cannot use `FieldMappingOrderingFilter` on a view which does not have a '
                          '`ordering_field_mappings` attribute configured.'))

    def test_improperly_configured_attribute_ordering_field_mappings(self):
        # Creating an inline ViewSet class.
        class MyViewSet(GenericViewSet, ListModelMixin):
            queryset = Signal.objects.all()
            pagination_class = LimitOffsetPagination
            serializer_class = SignalAuthHALSerializer
            filter_backends = (FieldMappingOrderingFilter, )
            ordering_fields = (
                'created_at',
                'address',
            )
            ordering_field_mappings = {
                'created_at': 'created_at',
                'xxx_address': 'address',  # mismatch with `ordering_fields`
            }

        # Creating a fake request to initiate the view.
        view = MyViewSet.as_view({'get': 'list'})

        with self.assertRaises(ImproperlyConfigured) as exp:
            view(self.fake_request_ordering)
        self.assertEqual(str(exp.exception),
                         ('Cannot use `FieldMappingOrderingFilter` on a view which does not have '
                          'defined all fields in `ordering_fields` in the corresponding '
                          '`ordering_field_mappings` attribute.'))


class TestSubSlugFilter(APITestCase):
    def setUp(self):
        # Assumes initial data in form of categories is present. (Possibly generalize this test
        # by not assuming a set category).
        self.sub_cat_1 = SubCategory.objects.get(slug='asbest-accu')
        self.sub_cat_2 = SubCategory.objects.get(slug='oever-kade-steiger')

        self.s1 = SignalFactory.create(category_assignment__sub_category=self.sub_cat_1)
        self.s2 = SignalFactory.create(category_assignment__sub_category=self.sub_cat_2)

        # We are testing the authenticated part of the API, hence:
        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)

    def test_filter_on_sub_slug(self):
        payload = {'sub_slug': self.sub_cat_1.slug}
        url = f'{SIGNAL_ENDPOINT}?{urlencode(payload)}'
        response = self.client.get(url)
        json_response = response.json()

        self.assertEqual(Signal.objects.count(), 2)
        self.assertEqual(json_response['count'], 1)
        self.assertEqual(
            json_response['results'][0]['category']['sub_slug'],
            self.s1.category_assignment.sub_category.slug
        )

    def test_backwards_compatibility(self):
        # Note: only relevant as long as we keep the category__sub filter.
        payload = {'sub_slug': self.sub_cat_1.slug}
        url = f'{SIGNAL_ENDPOINT}?{urlencode(payload)}'
        response = self.client.get(url)
        json_response_new = response.json()

        payload = {'category__sub': self.sub_cat_1.name}
        url = f'{SIGNAL_ENDPOINT}?{urlencode(payload)}'
        response = self.client.get(url)
        json_response_old = response.json()

        self.assertEqual(Signal.objects.count(), 2)
        self.assertEqual(json_response_new['count'], 1)
        self.assertEqual(json_response_old['count'], 1)

        self.assertEqual(
            json_response_new['results'][0]['id'],
            json_response_old['results'][0]['id']
        )


class TestMainSlugFilter(APITestCase):
    def setUp(self):
        # Assumes initial data in form of categories is present. (Possibly generalize this test
        # by not assuming a set category).
        self.main_cat_1 = MainCategory.objects.get(slug='afval')
        self.main_cat_2 = MainCategory.objects.get(slug='openbaar-groen-en-water')

        self.s1 = SignalFactory.create(
            category_assignment__sub_category__main_category=self.main_cat_1)
        self.s2 = SignalFactory.create(
            category_assignment__sub_category__main_category=self.main_cat_2)

        # We are testing the authenticated part of the API, hence:
        superuser = SuperUserFactory.create()
        self.client.force_authenticate(user=superuser)

    def test_filter_on_main_slug(self):
        payload = {'main_slug': self.main_cat_1.slug}
        url = f'{SIGNAL_ENDPOINT}?{urlencode(payload)}'
        response = self.client.get(url)
        json_response = response.json()

        self.assertEqual(Signal.objects.count(), 2)
        self.assertEqual(json_response['count'], 1)
        self.assertEqual(
            json_response['results'][0]['category']['main_slug'],
            self.s1.category_assignment.sub_category.main_category.slug
        )

    def test_backwards_compatibility(self):
        # Note: only relevant as long as we keep the category__main filter.
        payload = {'main_slug': self.main_cat_1.slug}
        url = f'{SIGNAL_ENDPOINT}?{urlencode(payload)}'
        response = self.client.get(url)
        json_response_new = response.json()

        payload = {'category__main': self.main_cat_1.name}
        url = f'{SIGNAL_ENDPOINT}?{urlencode(payload)}'
        response = self.client.get(url)
        json_response_old = response.json()

        self.assertEqual(Signal.objects.count(), 2)
        self.assertEqual(json_response_new['count'], 1)
        self.assertEqual(json_response_old['count'], 1)

        self.assertEqual(
            json_response_new['results'][0]['id'],
            json_response_old['results'][0]['id']
        )
