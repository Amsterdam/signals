from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from signals.apps.signals.models import CategoryAssignment, Signal
from tests.apps.signals.factories import CategoryFactory, SignalFactory


class TestSignalManager(TestCase):

    def setUp(self):
        self.signal = SignalFactory()
        self.category = CategoryFactory()
        self.category_assignment = CategoryAssignment.objects.create(category=self.category,
                                                                     _signal_id=self.signal.id)

    @patch("signals.apps.signals.models.CategoryAssignment.objects.create")
    def test_update_category_assignment(self, cat_assignment_create):
        cat_assignment_create.return_value = self.category_assignment

        Signal.actions.update_category_assignment({"category": self.category}, self.signal)

        # Should create an assignment
        cat_assignment_create.assert_called_once()
        cat_assignment_create.reset_mock()

        Signal.actions.update_category_assignment({"category": self.category}, self.signal)

        # Update with the same category should not create a new assignment
        cat_assignment_create.assert_not_called()

    def test_update_category_assignment_invalid_data(self):
        with self.assertRaises(ValidationError) as ve:
            Signal.actions.update_category_assignment({"yrogetac": self.category}, self.signal)

        self.assertEqual(ve.exception.message, 'Category not found in data')

    def test_update_multiple_invalid_category_data(self):
        with self.assertRaises(ValidationError) as ve:
            Signal.actions.update_multiple(
                {'category_assignment': {'yrogetac': self.category}},
                self.signal
            )

        self.assertEqual(ve.exception.message, 'Category not found in data')
