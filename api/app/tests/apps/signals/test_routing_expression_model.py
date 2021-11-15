# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.core.exceptions import ValidationError
from django.test import TestCase

from signals.apps.signals.factories import DepartmentFactory, ExpressionFactory
from signals.apps.signals.models import RoutingExpression
from signals.apps.users.factories import UserFactory


class TestRoutingExpression(TestCase):
    def test_routing_expression_with_valid_user_and_active(self):
        department = DepartmentFactory.create()
        expression = ExpressionFactory.create()
        user = UserFactory.create()
        user.profile.departments.add(department)

        routing_expression = RoutingExpression(
            _expression=expression,
            _department=department,
            _user=user,
            order=1,
            is_active=True,
        )
        routing_expression.save()

        self.assertEqual(routing_expression._department_id, department.id)
        self.assertEqual(routing_expression._user_id, user.id)

    def test_routing_expression_with_valid_user_and_not_active(self):
        department = DepartmentFactory.create()
        expression = ExpressionFactory.create()
        user = UserFactory.create()
        user.profile.departments.add(department)

        routing_expression = RoutingExpression(
            _expression=expression,
            _department=department,
            _user=user,
            order=1,
            is_active=False,
        )
        routing_expression.save()

        self.assertEqual(routing_expression._department_id, department.id)
        self.assertEqual(routing_expression._user_id, user.id)

    def test_routing_expression_with_invalid_user_and_active(self):
        department = DepartmentFactory.create()
        expression = ExpressionFactory.create()
        user = UserFactory.create()

        routing_expression = RoutingExpression(
            _expression=expression,
            _department=department,
            _user=user,
            order=1,
            is_active=True,
        )

        with self.assertRaises(ValidationError):
            routing_expression.save()

    def test_routing_expression_with_invalid_user_and_update_active(self):
        department = DepartmentFactory.create()
        expression = ExpressionFactory.create()
        user = UserFactory.create()

        routing_expression = RoutingExpression(
            _expression=expression,
            _department=department,
            _user=user,
            order=1,
            is_active=False,
        )
        routing_expression.save()

        self.assertEqual(routing_expression._department_id, department.id)
        self.assertEqual(routing_expression._user_id, user.id)

        routing_expression.is_active = True
        with self.assertRaises(ValidationError):
            routing_expression.save()
