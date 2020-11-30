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


class TestRoutingMechanism(TestCase):
    dsl_service = SignalDslService()

    def setUp(self):
        geometry = geos.MultiPolygon([geos.Polygon.from_bbox([4.877157, 52.357204, 4.929686, 52.385239])], srid=4326)
        self.area = AreaFactory.create(geometry=geometry, name='centrum', code='centrum', _type__code='stadsdeel')

        self.exp_routing_type = ExpressionTypeFactory.create(name="routing")
        self.department = DepartmentFactory.create()
        self.location_expr = ExpressionFactory.create(
            _type=self.exp_routing_type,
            name="test outside",
            code=f'location in areas."{self.area._type.name}"."{self.area.code}"'
        )

        RoutingExpressionFactory.create(
            _expression=self.location_expr,
            _department=self.department,
            is_active=True
        )

    def test_routing(self):
        # test signal outside center
        signal_outside = SignalFactory.create(
            location__geometrie=geos.Point(1.0, 1.0)
        )
        signal_outside.refresh_from_db()
        self.assertIsNone(signal_outside.routing_assignment)
        # simulate apply routing rules
        self.dsl_service.process_routing_rules(signal_outside)
        signal_outside.refresh_from_db()
        self.assertIsNone(signal_outside.routing_assignment)

        # test signal inside center
        signal_inside = SignalFactory.create(
            location__geometrie=geos.Point(4.88, 52.36)
        )
        signal_inside.refresh_from_db()
        self.assertIsNone(signal_inside.routing_assignment)
        # simulate apply routing rules
        self.dsl_service.process_routing_rules(signal_inside)
        signal_inside.refresh_from_db()
        self.assertIsNotNone(signal_inside.routing_assignment)
        self.assertEqual(len(signal_inside.routing_assignment.departments.all()), 1)
        routing_dep = signal_inside.routing_assignment.departments.first()
        self.assertEqual(routing_dep.id, self.department.id)
