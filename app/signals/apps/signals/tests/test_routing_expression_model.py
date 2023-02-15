# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.core.exceptions import ValidationError
from django.test import TestCase

from signals.apps.signals.factories import DepartmentFactory, ExpressionFactory
from signals.apps.signals.models import RoutingExpression
from signals.apps.users.factories import UserFactory


class TestRoutingExpression(TestCase):
    """
    A User can only be assigned to a RoutingExpression if it is a member of the Department that is set on the same
    RoutingExpression. Also the User must be active.
    """
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

        # User must be a member of the Department
        with self.assertRaises(ValidationError, msg=f'{user.username} is not part of department {department.name}'):
            routing_expression.save()

        # Inactivate User is not allowed
        user.profile.departments.add(department)
        user.is_active = False
        user.save()
        with self.assertRaises(ValidationError, msg=f'{user.username} is not active'):
            routing_expression.save()

    def test_routing_expression_with_invalid_user_and_update_active(self):
        """
        Validation of the User will only be triggered if a RoutingExpression is set to active.
        If a RoutingExpression is made with active is False and in the time between activation the User is no longer
        member of the associated Department this will trigger and the RoutingExpression must be fixed before saving.
        """
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

        # User must be a member of the Department
        routing_expression.is_active = True
        with self.assertRaises(ValidationError):
            routing_expression.save()

        # Inactivate User and not a member of the Department is not allowed
        user.is_active = False
        user.save()
        with self.assertRaises(ValidationError):
            routing_expression.save()

        # Inactivate User is not allowed
        user.profile.departments.add(department)
        with self.assertRaises(ValidationError):
            routing_expression.save()
