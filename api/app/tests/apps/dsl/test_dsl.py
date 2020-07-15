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
            'location': geos.Point(5, 23),
            'maincat': 'dieren',
            'subcat': 'subcat',
            'time': time.strptime("16:00:00", "%H:%M:%S"),
            'area': {
                'stadsdeel': {
                    'oost': geos.MultiPolygon(poly)
                }
            },
            'lijstval': 'geo1',
            'lijstje': set(['geo1', 'geo2'])
        }


    def test_numeric_equality(self):
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
