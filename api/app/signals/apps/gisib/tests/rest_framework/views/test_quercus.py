# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.test import override_settings
from django.urls import include, path
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase

from signals.apps.api.views import NamespaceView
from signals.apps.gisib.factories import BBOX, GISIBFeatureFactory

urlpatterns = [
    path('v1/relations/', NamespaceView.as_view(), name='signal-namespace'),
    path('', include('signals.apps.gisib.urls')),
]


class NameSpace:
    pass


test_urlconf = NameSpace()
test_urlconf.urlpatterns = urlpatterns


@override_settings(ROOT_URLCONF=test_urlconf)
class TestGISIBQuercusEndpoint(APITestCase):
    endpoint = '/public/gisib/quercus'

    def setUp(self):
        self.gisib_features = GISIBFeatureFactory.create_batch(5)

    def test_get_trees(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(5, len(response.json()['features']))

    def test_get_trees_filter_by_gisib_id(self):
        response = self.client.get(self.endpoint, data={'id': self.gisib_features[0].gisib_id})
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(1, len(response.json()['features']))

    def test_get_trees_filter_by_bbox(self):
        response = self.client.get(self.endpoint, data={'bbox': ','.join([str(f) for f in BBOX])})
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(5, len(response.json()['features']))


class TestGISIBQuercusEndpointDisabled(APITestCase):
    endpoint = '/public/gisib/quercus'

    def setUp(self):
        GISIBFeatureFactory.create_batch(5)

    def test_get_trees(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(HTTP_404_NOT_FOUND, response.status_code)
