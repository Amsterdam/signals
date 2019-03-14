from unittest.mock import patch

from django.test import TestCase

from signals.apps.signals.models import CategoryAssignment, Signal
from tests.apps.signals.factories import SignalFactory, SubCategoryFactory


class TestSignalManager(TestCase):

    def setUp(self):
        self.signal = SignalFactory()
        self.category = SubCategoryFactory()
        self.category_assignment = CategoryAssignment.objects.create(sub_category=self.category,
                                                                     _signal_id=self.signal.id)

    @patch("signals.apps.signals.models.CategoryAssignment.objects.create")
    def test_update_category_assignment(self, cat_assignment_create):
        cat_assignment_create.return_value = self.category_assignment

        Signal.actions.update_category_assignment({"sub_category": self.category}, self.signal)

        # Should create an assignment
        cat_assignment_create.assert_called_once()
        cat_assignment_create.reset_mock()

        Signal.actions.update_category_assignment({"sub_category": self.category}, self.signal)

        # Update with the same category should not create a new assignment
        cat_assignment_create.assert_not_called()
