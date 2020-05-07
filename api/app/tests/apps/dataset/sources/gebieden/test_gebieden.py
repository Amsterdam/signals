import json
import os
from os.path import join

import requests
import requests_mock
from django.contrib.gis.geos import LinearRing, MultiPolygon, Polygon
from django.test import TestCase

from signals.apps.dataset.sources.gebieden import APIGebiedenLoader, GebiedenAPIGeometryLoader
from signals.apps.signals.models import Area

THIS_DIR = os.path.dirname(__file__)
RD_STADHUIS = [121853, 486780]
WGS84_BBOX_AMSTERDAM = [
    [4.58565, 52.03560],
    [4.58565, 52.48769],
    [5.31360, 52.48769],
    [5.31360, 52.03560],
    [4.58565, 52.03560],
]


class TestGebiedenAPIGeometryLoader(TestCase):
    def setUp(self):
        # Test with a 10 meter square in Amsterdam Cityhall / Opera
        x, y = RD_STADHUIS
        width, height = 10, 10
        self.polygon_1 = [[
            [x, y],
            [x + width, y],
            [x + width, y + height],
            [x, y + height],
            [x, y]
        ]]
        self.polygon_2 = [[
            [x + width, y],
            [x + 2 * width, y],
            [x + 2 * width, y + height],
            [x + width, y + height],
            [x + width, y]
        ]]
        self.gl = GebiedenAPIGeometryLoader()

    def test_load_polygon(self):
        polygon = self.gl.load_polygon(self.polygon_1)
        self.assertIsInstance(polygon, Polygon)
        self.assertEqual(polygon.srid, 28992)

    def test_load_multipolygon(self):
        multi_polygon = self.gl.load_multipolygon(
            [self.polygon_1, self.polygon_2]
        )
        self.assertIsInstance(multi_polygon, MultiPolygon)
        self.assertEqual(multi_polygon.srid, 28992)

    def test_RD_to_WGS84_conversion(self):
        # Crude test, we check that Amsterdam Cityhall lies within a larger
        # Amsterdam bounding box we took from the factories file. All this in
        # WGS84 coordinates.
        polygon = self.gl.load_polygon(self.polygon_1)
        bbox_020 = Polygon(LinearRing(WGS84_BBOX_AMSTERDAM, srid=4326), srid=4326)
        self.assertEqual(bbox_020.srid, 4326)

        polygon.transform(ct=4326)
        self.assertTrue(bbox_020.contains(polygon))


class TestAPIGebiedenLoader(TestCase):
    def setUp(self):
        self.session = requests.Session()
        self.adapter = requests_mock.Adapter()
        self.session.mount('https://', self.adapter)

        APIGebiedenLoader._get_session = lambda instance: self.session
        self.api_loader = APIGebiedenLoader('stadsdeel')

        # We mock the API output using some saved API output (edited to have
        # only two stadsdeel instances).
        self.centrum_url = 'https://api.data.amsterdam.nl/gebieden/stadsdeel/03630000000018/'
        self.zuidoost_url = 'https://api.data.amsterdam.nl/gebieden/stadsdeel/03630000000016/'
        self.list_endpoint = 'https://api.data.amsterdam.nl/gebieden/stadsdeel/'
        self.page_1_url = 'https://api.data.amsterdam.nl/gebieden/stadsdeel/?page_size=1'
        self.page_2_url = 'https://api.data.amsterdam.nl/gebieden/stadsdeel/?page=2&page_size=1'
        url_json_mapping = [
            (self.centrum_url, 'centrum.json'),
            (self.zuidoost_url, 'zuidoost.json'),
            (self.page_1_url, 'gebieden_page_1.json'),
            (self.list_endpoint, 'gebieden_page_1.json'),  # first page serves as stand-in for list endpoint
            (self.page_2_url, 'gebieden_page_2.json'),
        ]

        for url, json_file in url_json_mapping:
            with open(join(THIS_DIR, json_file), 'r') as f:
                data = json.load(f)
                self.adapter.register_uri('GET', url, json=data)

    def test__load_area_detail(self):
        self.assertEqual(Area.objects.count(), 0)
        self.api_loader._load_area_detail(self.session, self.centrum_url)

        # Check that Centrum was correctly loaded from API output.
        self.assertEqual(Area.objects.count(), 1)
        area = Area.objects.first()
        self.assertEqual(area.name, 'Centrum')  # see: centrum.json
        self.assertEqual(area.geometry.srid, 4326)

    def test__iter_urls(self):
        urls = list(self.api_loader._iterate_urls(self.session, self.page_1_url))
        self.assertEqual(urls, [
            'https://api.data.amsterdam.nl/gebieden/stadsdeel/03630000000016/',
            'https://api.data.amsterdam.nl/gebieden/stadsdeel/03630000000018/',
        ])

    def test_load(self):
        self.assertEqual(Area.objects.count(), 0)
        self.api_loader.load()
        created_areas = set(Area.objects.all().values_list('name', flat=True))
        self.assertEqual(created_areas, set(['Centrum', 'Zuidoost']))

    def test__get_session(self):
        agl = APIGebiedenLoader('stadsdeel')
        session = agl._get_session()
        self.assertIsInstance(session, requests.Session)
