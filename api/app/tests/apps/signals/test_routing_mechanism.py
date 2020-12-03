from django.contrib.gis import geos
from django.test import TestCase

from signals.apps.services.domain.dsl import SignalContext, SignalDslService
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
        self.assertIsNstort
    def test_context_func(self):
        # test signal outside center
        signal = SignalFactory.create()
        signal.extra_properties = [
            {
                "id": "key1",
                "answer": {
                    "id": "2",
                    "info": "",
                    "label": "value 1"
                },
            },
            {
                "id": "key2",
                "answer": {
                    "id": "2",
                    "info": "",
                    "value": "value 2"
                },
            },
            {
                "id": "key3_list",
                "answer": [
                    {
                        "id": "2",
                        "label": "value 3.1"
                    },
                    {
                        "id": "3",
                        "label": "value 3.2"
                    }
                ],
            },
            {
                "id": "key4",
                "answer": "value 4",
            }
        ]

        ctx_func = SignalContext()
        ctx = ctx_func(signal)
        self.assertEqual(ctx['key1'], "value 1")
        self.assertEqual(ctx['key2'], "value 2")
        self.assertEqual(type(ctx['key3_list']), set)
        self.assertTrue("value 3.1" in ctx['key3_list'])
        self.assertTrue("value 3.2" in ctx['key3_list'])
        self.assertEqual(ctx['key4'], "value 4")
