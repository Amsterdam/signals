# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
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
    dsl_service = SignalDslService()

    def setUp(self):
        geometry = geos.MultiPolygon([geos.Polygon.from_bbox([4.877157, 52.357204, 4.929686, 52.385239])], srid=4326)
        self.area = AreaFactory.create(
            geometry=geometry,
            name='centrum',
            code='centrum',
            _type__name='gebied',
            _type__code='stadsdeel')

        self.exp_routing_type = ExpressionTypeFactory.create(name="routing")
        self.department = DepartmentFactory.create()
        self.location_expr = ExpressionFactory.create(
            _type=self.exp_routing_type,
            name="test outside",
            code=f'location in areas."{self.area._type.name}"."{self.area.code}"'
        )

        self.user = UserFactory.create()

        RoutingExpressionFactory.create(
            _expression=self.location_expr,
            _department=self.department,
            _user=self.user,
            is_active=True,
            order=2
        )

    def test_routing_with_user(self):
        signal = SignalFactory.create(
            location__geometrie=geos.Point(4.88, 52.36)
        )
        signal.refresh_from_db()
        self.assertIsNone(signal.user_assignment)
        self.assertIsNone(signal.routing_assignment)
        # simulate apply routing rules
        self.dsl_service.process_routing_rules(signal)
        signal.refresh_from_db()
        self.assertIsNotNone(signal.user_assignment)
        self.assertIsNotNone(signal.routing_assignment)
        user = signal.user_assignment.user
        self.assertEqual(user.id, self.user.id)
