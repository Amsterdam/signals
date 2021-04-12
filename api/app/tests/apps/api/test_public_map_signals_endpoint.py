# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import os

from django.test import override_settings

from signals.apps.api.urls_v1 import SignalsRouterVersion1
from signals.apps.api.views import PublicSignalMapViewSet
from signals.apps.signals.factories import SignalFactoryValidLocation
from tests.test import SignalsBaseApiTestCase

THIS_DIR = os.path.dirname(__file__)


class NameSpace():
    pass


# we need to simulate a new route or unit test, urls.py is evaluated once, and cannot be unit tested with settings
# we set a custom route for the unit test only
extra_router = SignalsRouterVersion1()
extra_router.register(r'public/map-signals', PublicSignalMapViewSet, basename='public-list-signals')
test_urlconf = NameSpace()
test_urlconf.urlpatterns = extra_router.urls


@override_settings(ROOT_URLCONF=test_urlconf)
class TestMapSignalEndpoints(SignalsBaseApiTestCase):
    def setUp(self):
        self.endpoint_url = '/public/map-signals/'
        self.signal1 = SignalFactoryValidLocation.create()
        self.signal2 = SignalFactoryValidLocation.create()
        super().setUp()

    def test_map_signals_list(self):
        response = self.client.get(self.endpoint_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['features']), 2)
        datadict = {feature['properties']['id']: feature for feature in data['features']}
        obj = datadict[self.signal1.id]
        self.assertEqual(round(obj['geometry']['coordinates'][0], 5), round(self.signal1.location.geometrie.x, 5))
        self.assertEqual(round(obj['geometry']['coordinates'][1], 5), round(self.signal1.location.geometrie.y, 5))
        self.assertEqual(obj['properties']['status'], self.signal1.status.state)
        self.assertEqual(obj['properties']['category']['main'], self.signal1.category_assignment.category.parent.name) # noqa
        self.assertEqual(obj['properties']['category']['sub'], self.signal1.category_assignment.category.name)
        obj = datadict[self.signal2.id]
        self.assertEqual(round(obj['geometry']['coordinates'][0], 5), round(self.signal2.location.geometrie.x, 5))
        self.assertEqual(round(obj['geometry']['coordinates'][1], 5), round(self.signal2.location.geometrie.y, 5))
        self.assertEqual(obj['properties']['status'], self.signal2.status.state)
        self.assertEqual(obj['properties']['category']['main'], self.signal2.category_assignment.category.parent.name) # noqa
        self.assertEqual(obj['properties']['category']['sub'], self.signal2.category_assignment.category.name)


class TestMapSignalDefaultSettingEndpoints(SignalsBaseApiTestCase):
    def test_map_signals_list_defalt(self):
        # Default configuration has this endpoint disabled by removing it from the URL definitions.
        response = self.client.get('/signals/v1/public/map-signals/')
        self.assertEqual(response.status_code, 404)
