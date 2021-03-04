# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import time

from django.contrib.gis import geos
from django.test import TestCase

from signals.apps.dsl.ExpressionEvaluator import ExpressionEvaluator


class DslTest(TestCase):
    def setUp(self):
        self.compiler = ExpressionEvaluator()
        poly = geos.Polygon(
            ((0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0), (0.0, 0.0))
        )

        self.context = {
            'testint': 1,
            'location_1': geos.Point(66, 66),
            'location_2': geos.Point(1, 1),
            'maincat': 'dieren',
            'subcat': 'subcat',
            'time': time.strptime("16:00:00", "%H:%M:%S"),
            'area': {
                'stadsdeel': {
                    'oost': geos.MultiPolygon(poly)
                }
            },
            'listval': 'geo1',
            'list': set(['geo1', 'geo2'])
        }

    def test_numeric_operations(self):
        c = self.compiler
        self.assertTrue(c.compile('testint == 1').evaluate(self.context))
        self.assertFalse(c.compile('testint == 0').evaluate(self.context))

        self.assertFalse(c.compile('testint != 1').evaluate(self.context))
        self.assertTrue(c.compile('testint != 0').evaluate(self.context))

        self.assertFalse(c.compile('testint > 1').evaluate(self.context))
        self.assertTrue(c.compile('testint >= 1').evaluate(self.context))
        self.assertTrue(c.compile('testint > 0').evaluate(self.context))
        self.assertTrue(c.compile('testint >= 0').evaluate(self.context))
        self.assertFalse(c.compile('testint > 2').evaluate(self.context))
        self.assertFalse(c.compile('testint >= 2').evaluate(self.context))

        self.assertFalse(c.compile('testint < 1').evaluate(self.context))
        self.assertTrue(c.compile('testint <= 1').evaluate(self.context))
        self.assertFalse(c.compile('testint < 0').evaluate(self.context))
        self.assertFalse(c.compile('testint <= 0').evaluate(self.context))
        self.assertTrue(c.compile('testint < 2').evaluate(self.context))
        self.assertTrue(c.compile('testint <= 2').evaluate(self.context))

    def test_time_operations(self):
        c = self.compiler
        self.assertTrue(c.compile('time == 16:00:00').evaluate(self.context))
        self.assertFalse(c.compile('time == 16:00:01').evaluate(self.context))

        self.assertFalse(c.compile('time != 16:00:00').evaluate(self.context))
        self.assertTrue(c.compile('time != 16:00:01').evaluate(self.context))

        self.assertFalse(c.compile('time > 16:00:00').evaluate(self.context))
        self.assertTrue(c.compile('time >= 16:00:00').evaluate(self.context))
        self.assertTrue(c.compile('time > 15:00:00').evaluate(self.context))
        self.assertTrue(c.compile('time >= 15:00:00').evaluate(self.context))
        self.assertFalse(c.compile('time > 16:00:01').evaluate(self.context))
        self.assertFalse(c.compile('time >= 16:00:01').evaluate(self.context))

        self.assertFalse(c.compile('time < 16:00:00').evaluate(self.context))
        self.assertTrue(c.compile('time <= 16:00:00').evaluate(self.context))
        self.assertFalse(c.compile('time < 15:00:00').evaluate(self.context))
        self.assertFalse(c.compile('time <= 15:00:00').evaluate(self.context))
        self.assertTrue(c.compile('time < 16:00:01').evaluate(self.context))
        self.assertTrue(c.compile('time <= 16:00:01').evaluate(self.context))

    def test_string_operations(self):
        c = self.compiler
        self.assertFalse(c.compile('maincat == "test"').evaluate(self.context))
        self.assertTrue(c.compile('maincat == "dieren"').evaluate(self.context))
        self.assertTrue(c.compile('maincat != "test"').evaluate(self.context))
        self.assertFalse(c.compile('maincat != "dieren"').evaluate(self.context))

    def test_in_collection_operations(self):
        c = self.compiler
        self.assertTrue(c.compile('listval in list').evaluate(self.context))
        self.assertFalse(c.compile('maincat in list').evaluate(self.context))

    def test_in_gemometry_operations(self):
        c = self.compiler
        self.assertFalse(c.compile('location_1 in area."stadsdeel"."oost"').evaluate(self.context))
        self.assertTrue(c.compile('location_2 in area."stadsdeel"."oost"').evaluate(self.context))

    def test_and_or(self):
        c = self.compiler
        self.assertTrue(c.compile('testint == 0 or testint == 1').evaluate(self.context))
        self.assertFalse(c.compile('testint == 0 and testint == 1').evaluate(self.context))
        self.assertTrue(c.compile('testint == 1 and (time > 12:00 and time < 20:00)').evaluate(self.context))
        self.assertTrue(c.compile('testint == 1 or (time > 12:00 and time < 20:00)').evaluate(self.context))
        self.assertTrue(c.compile(
            'location_2 in area."stadsdeel"."oost" and (testint > 0 or (testint == 1))'
        ).evaluate(self.context))
        self.assertFalse(c.compile('maincat in list and (time > 12:00 and time < 20:00)').evaluate(self.context))

    def test_grammer_multiple_and_or(self):
        c = self.compiler
        c.compile('testint == 0 or testint == 1 or testint == 2')
        c.compile('testint == 0 and testint == 1 and testint == 2')
        c.compile('testint == 0 and testint == 1 or testint == 2')
        c.compile('testint == 0 or testint == 1 and testint == 2')
