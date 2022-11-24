# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from django.contrib.gis import geos
from django.test import TestCase

from signals.apps.services.domain.dsl import SignalDslService
from signals.apps.signals.factories import (
    AreaFactory,
    DepartmentFactory,
    ExpressionFactory,
    ExpressionTypeFactory,
    RoutingExpressionFactory,
    SignalFactory
)
from signals.apps.users.factories import UserFactory


class TestRoutingMechanism(TestCase):
    def test_routing_with_user(self):
        department = DepartmentFactory.create()
        user = UserFactory.create()
        user.profile.departments.add(department)

        geometry = geos.MultiPolygon([geos.Polygon.from_bbox([4.877157, 52.357204, 4.929686, 52.385239])], srid=4326)
        area = AreaFactory.create(geometry=geometry, name='centrum', code='centrum', _type__name='gebied',
                                  _type__code='stadsdeel')

        expression_routing_type = ExpressionTypeFactory.create(name="routing")
        expression = ExpressionFactory.create(_type=expression_routing_type, name="test outside",
                                              code=f'location in areas."{area._type.name}"."{area.code}"')

        RoutingExpressionFactory.create(_expression=expression, _department=department, _user=user)

        signal = SignalFactory.create(location__geometrie=geos.Point(4.88, 52.36))
        self.assertIsNone(signal.user_assignment)

        # simulate applying routing rules
        dsl_service = SignalDslService()

        dsl_service.process_routing_rules(signal, 'TEST_PLACEHOLDER')

        signal.refresh_from_db()
        self.assertEqual(signal.user_assignment.user.id, user.id)

    def test_routing_with_user_no_longer_member_of_department(self):
        department = DepartmentFactory.create()
        user = UserFactory.create()
        user.profile.departments.add(department)

        geometry = geos.MultiPolygon([geos.Polygon.from_bbox([4.877157, 52.357204, 4.929686, 52.385239])], srid=4326)
        area = AreaFactory.create(geometry=geometry, name='centrum', code='centrum', _type__name='gebied',
                                  _type__code='stadsdeel')

        expression_routing_type = ExpressionTypeFactory.create(name="routing")
        expression = ExpressionFactory.create(_type=expression_routing_type, name="test outside",
                                              code=f'location in areas."{area._type.name}"."{area.code}"')

        routing_expression = RoutingExpressionFactory.create(_expression=expression, _department=department, _user=user)
        self.assertTrue(routing_expression.is_active)

        # In the mean time the user is no longer part of the department
        user.profile.departments.remove(department)

        signal = SignalFactory.create(location__geometrie=geos.Point(4.88, 52.36))
        self.assertIsNone(signal.user_assignment)

        # simulate applying routing rules
        dsl_service = SignalDslService()

        dsl_service.process_routing_rules(signal, 'TEST_PLACEHOLDER')

        signal.refresh_from_db()
        self.assertIsNone(signal.user_assignment)

        routing_expression.refresh_from_db()
        self.assertFalse(routing_expression.is_active)

    def test_routing_with_user_no_longer_active(self):
        department = DepartmentFactory.create()
        user = UserFactory.create()
        user.profile.departments.add(department)

        geometry = geos.MultiPolygon([geos.Polygon.from_bbox([4.877157, 52.357204, 4.929686, 52.385239])], srid=4326)
        area = AreaFactory.create(geometry=geometry, name='centrum', code='centrum', _type__name='gebied',
                                  _type__code='stadsdeel')

        expression_routing_type = ExpressionTypeFactory.create(name="routing")
        expression = ExpressionFactory.create(_type=expression_routing_type, name="test outside",
                                              code=f'location in areas."{area._type.name}"."{area.code}"')

        routing_expression = RoutingExpressionFactory.create(_expression=expression, _department=department, _user=user)
        self.assertTrue(routing_expression.is_active)

        # In the mean time the user has been deactived
        user.is_active = False
        user.save()

        signal = SignalFactory.create(location__geometrie=geos.Point(4.88, 52.36))
        self.assertIsNone(signal.user_assignment)

        # simulate applying routing rules
        dsl_service = SignalDslService()

        dsl_service.process_routing_rules(signal, 'TEST_PLACEHOLDER')

        signal.refresh_from_db()
        self.assertIsNone(signal.user_assignment)

        routing_expression.refresh_from_db()
        self.assertFalse(routing_expression.is_active)
