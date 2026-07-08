# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Delta10 B.V.

from django.contrib.gis import geos
from django.core.cache import cache
from django.test import TestCase, override_settings
from import_export.signals import post_import

from signals.apps.services.domain.dsl import SignalContext, SignalDslService
from signals.apps.signals.area_cache import get_area_cache_version
from signals.apps.signals.factories import (
    AreaFactory,
    AreaTypeFactory,
    DepartmentFactory,
    ExpressionFactory,
    ExpressionTypeFactory,
    RoutingExpressionFactory,
    SignalFactory
)
from signals.apps.signals.models import Area, AreaType


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'area-cache-invalidation-tests',
    }
})
class AreaCacheInvalidationTest(TestCase):
    def setUp(self):
        cache.clear()

    def test_area_save_invalidates_area_cache_version(self):
        area = AreaFactory.create()
        version_before = get_area_cache_version()

        area.name = 'Updated area'
        with self.captureOnCommitCallbacks(execute=True):
            area.save()

        self.assertNotEqual(get_area_cache_version(), version_before)

    def test_area_delete_invalidates_area_cache_version(self):
        area = AreaFactory.create()
        version_before = get_area_cache_version()

        with self.captureOnCommitCallbacks(execute=True):
            area.delete()

        self.assertNotEqual(get_area_cache_version(), version_before)

    def test_area_post_import_invalidates_area_cache_version(self):
        version_before = get_area_cache_version()

        with self.captureOnCommitCallbacks(execute=True):
            post_import.send(sender=None, model=Area)

        self.assertNotEqual(get_area_cache_version(), version_before)

    def test_area_type_save_invalidates_area_cache_version(self):
        area_type = AreaTypeFactory.create()
        version_before = get_area_cache_version()

        area_type.name = 'Updated area type'
        with self.captureOnCommitCallbacks(execute=True):
            area_type.save()

        self.assertNotEqual(get_area_cache_version(), version_before)

    def test_area_type_delete_invalidates_area_cache_version(self):
        area_type = AreaTypeFactory.create()
        version_before = get_area_cache_version()

        with self.captureOnCommitCallbacks(execute=True):
            area_type.delete()

        self.assertNotEqual(get_area_cache_version(), version_before)

    def test_area_type_post_import_invalidates_area_cache_version(self):
        version_before = get_area_cache_version()

        with self.captureOnCommitCallbacks(execute=True):
            post_import.send(sender=None, model=AreaType)

        self.assertNotEqual(get_area_cache_version(), version_before)

    def test_signal_context_reloads_areas_after_invalidation(self):
        area = AreaFactory.create(code='old-code', _type__name='gebied', _type__code='gebied')
        context = SignalContext()

        self.assertIn('old-code', context.areas['gebied'])

        area.code = 'new-code'
        with self.captureOnCommitCallbacks(execute=True):
            area.save()

        self.assertIn('new-code', context.areas['gebied'])
        self.assertNotIn('old-code', context.areas['gebied'])

    def test_routing_uses_updated_area_without_recreating_service(self):
        area = AreaFactory.create(
            geometry=geos.MultiPolygon([geos.Polygon.from_bbox([1.0, 1.0, 2.0, 2.0])], srid=4326),
            name='centrum',
            code='centrum',
            _type__name='gebied',
            _type__code='gebied'
        )
        expression_type = ExpressionTypeFactory.create(name='routing')
        department = DepartmentFactory.create()
        expression = ExpressionFactory.create(
            _type=expression_type,
            code='location in areas."gebied"."centrum"'
        )
        RoutingExpressionFactory.create(
            _expression=expression,
            _department=department,
            is_active=True,
            order=1
        )
        signal = SignalFactory.create(location__geometrie=geos.Point(4.88, 52.36, srid=4326))
        service = SignalDslService()
        service.context_func = SignalContext()

        self.assertFalse(service.process_routing_rules(signal))
        signal.refresh_from_db()
        self.assertIsNone(signal.routing_assignment)

        area.geometry = geos.MultiPolygon([geos.Polygon.from_bbox([4.87, 52.35, 4.89, 52.37])], srid=4326)
        with self.captureOnCommitCallbacks(execute=True):
            area.save()

        self.assertTrue(service.process_routing_rules(signal))
        signal.refresh_from_db()
        self.assertIsNotNone(signal.routing_assignment)
        self.assertEqual(signal.routing_assignment.departments.first(), department)
