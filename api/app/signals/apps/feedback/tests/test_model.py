# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from signals.apps.feedback.app_settings import FEEDBACK_EXPECTED_WITHIN_N_DAYS
from signals.apps.feedback.factories import FeedbackFactory
from signals.apps.feedback.models import _get_description_of_receive_feedback


class TestFeedbackModel(TestCase):

    def setUp(self):
        self.feedback = FeedbackFactory.create()

    def test_is_to_late(self):
        """
        Check if the created date is later then the FEEDBACK_EXPECTED_WITHIN_N_DAYS
        """
        timedelta(days=FEEDBACK_EXPECTED_WITHIN_N_DAYS + 1)
        self.feedback.created_at = timezone.now() - timedelta(days=FEEDBACK_EXPECTED_WITHIN_N_DAYS + 1)
        self.assertTrue(self.feedback.is_too_late)

    def test_is_not_to_late(self):
        """
        Check if the created date is later then the FEEDBACK_EXPECTED_WITHIN_N_DAYS
        """
        self.assertFalse(self.feedback.is_too_late)

    def test_is_filled_out(self):
        self.feedback.submitted_at = timezone.now()
        self.assertTrue(self.feedback.is_filled_out)

    def test_is_not_filled_out(self):
        self.assertFalse(self.feedback.is_filled_out)


class TestDescriptionReceived(TestCase):

    def test__get_description_of_receive_feedback(self):
        feedback = FeedbackFactory.create(
            is_satisfied=True,
            text=None,
            text_list=['my', 'test', 'list'],
            text_extra='extra_text',
            allows_contact=True,
        )
        response = _get_description_of_receive_feedback(feedback.token)
        validate_text = "Ja, de melder is tevreden\nWaarom: my,test,list\nToelichting: extra_text\n" \
                        "Toestemming contact opnemen: Ja"
        self.assertEqual(response, validate_text)

    def test__get_description_of_receive_feedback_no_satisfied(self):
        feedback = FeedbackFactory.create(
            is_satisfied=False,
            text="My Text",
            text_list=None,
            text_extra=None,
            allows_contact=False,
        )
        response = _get_description_of_receive_feedback(feedback.token)
        validate_text = "Nee, de melder is ontevreden\nWaarom: My Text\n" \
                        "Toestemming contact opnemen: Nee"
        self.assertEqual(response, validate_text)
