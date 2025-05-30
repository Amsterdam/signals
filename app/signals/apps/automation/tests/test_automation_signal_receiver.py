from unittest.mock import patch

from django.test import TestCase

from signals.apps.automation.signal_receivers import create_initial_handler
from signals.apps.signals.factories import ParentCategoryFactory, CategoryFactory, SignalFactory
from signals.apps.signals.managers import create_initial


class TestAutomationSignalReceiver(TestCase):
    """Test the create_initial signal receiver."""
    def setUp(self):
        self.parent_category = ParentCategoryFactory.create()
        self.child_category = CategoryFactory.create(parent=self.parent_category, name="kerstbomen",
                                                     public_name='Kerstbomen',
                                                     is_public_accessible=True)

        self.signal = SignalFactory.create(category_assignment__category=self.child_category)

    @patch('signals.apps.automation.tasks.create_initial.delay')
    def test_create_initial_handler_calls_task(self, mock_task_delay):
        """Test that the receiver calls the Celery task with correct signal ID."""
        create_initial_handler(
            sender=None,
            signal_obj=self.signal,
        )

        mock_task_delay.assert_called_once_with(signal_id=self.signal.pk)

    @patch('signals.apps.automation.tasks.create_initial.delay')
    def test_create_initial_handler_with_signal_dispatch(self, mock_task_delay):
        """Test that the receiver works when triggered by Django signal."""
        create_initial.send(sender=None, signal_obj=self.signal)

        mock_task_delay.assert_called_once_with(signal_id=self.signal.pk)