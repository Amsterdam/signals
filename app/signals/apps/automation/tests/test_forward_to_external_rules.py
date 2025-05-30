# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Delta10 B.V.

from unittest.mock import patch, Mock
from django.test import TestCase

from signals.apps.automation import tasks
from signals.apps.automation.factories import ForwardToExternalFactory
from signals.apps.signals import workflow
from signals.apps.signals.factories import ExpressionTypeFactory, ExpressionFactory, \
    ParentCategoryFactory, CategoryFactory, SignalFactory


class TestForwardToExternalRules(TestCase):
    def setUp(self):
        self.parent_category = ParentCategoryFactory.create()
        self.child_category = CategoryFactory.create(parent=self.parent_category, name="kerstbomen", public_name='Kerstbomen',
                                                is_public_accessible=True)

        self.signal = SignalFactory.create(category_assignment__category=self.child_category)

        self.exp_routing_type = ExpressionTypeFactory.create()
        self.expression = ExpressionFactory.create(
            _type=self.exp_routing_type,
            name="sub:kerstbomen",
            code=f'sub == "kerstbomen"'
        )

        self.forward_to_external_rule = ForwardToExternalFactory.create(expression=self.expression)

    @patch('signals.apps.automation.tasks.Signal.actions.update_status')
    def test_forward_to_external_rule_matches_and_executes(self, mock_update_status):
        """Test that ForwardToExternal rule executes when expression matches."""
        tasks.create_initial(signal_id=self.signal.id)

        expected_status_data = {
            'text': self.forward_to_external_rule.text,  # Assuming the factory creates this
            'email_override': self.forward_to_external_rule.email,
            'send_email': True,
            'state': workflow.DOORGEZET_NAAR_EXTERN
        }

        mock_update_status.assert_called_once_with(expected_status_data, self.signal)

    @patch('signals.apps.automation.tasks.Signal.actions.update_status')
    def test_forward_to_external_rule_does_not_match(self, mock_update_status):
        """Test that ForwardToExternal rule doesn't execute when expression doesn't match."""
        different_category = CategoryFactory.create(name="not-kerstbomen", parent=self.parent_category)
        non_matching_signal = SignalFactory.create(category_assignment__category=different_category)

        tasks.create_initial(signal_id=non_matching_signal.id)

        mock_update_status.assert_not_called()

    @patch('signals.apps.automation.tasks.Signal.actions.update_status')
    @patch('signals.apps.automation.tasks.make_text_context')
    def test_forward_to_external_template_rendering(self, mock_make_context, mock_update_status):
        """Test that the template in ForwardToExternal rule renders correctly."""
        template_text = "Signal {{ signal.id }} forwarded from {{ category.name }}"
        self.forward_to_external_rule.text = template_text
        self.forward_to_external_rule.email = "test@external.com"
        self.forward_to_external_rule.save()

        mock_make_context.return_value = {
            'signal': {'id': self.signal.id},
            'category': {'name': self.child_category.name}
        }

        tasks.create_initial(signal_id=self.signal.id)

        expected_text = f"Signal {self.signal.id} forwarded from {self.child_category.name}"
        expected_status_data = {
            'text': expected_text,
            'email_override': "test@external.com",
            'send_email': True,
            'state': workflow.DOORGEZET_NAAR_EXTERN
        }

        mock_update_status.assert_called_once_with(expected_status_data, self.signal)
