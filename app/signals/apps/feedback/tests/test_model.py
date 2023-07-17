# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 - 2023 Gemeente Amsterdam

from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from signals.apps.feedback.app_settings import FEEDBACK_EXPECTED_WITHIN_N_DAYS
from signals.apps.feedback.factories import FeedbackFactory


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

    def test_get_description(self):
        feedback = FeedbackFactory.create(
            is_satisfied=True,
            text=None,
            text_list=['my', 'test', 'list'],
            text_extra='extra_text',
            allows_contact=True,
        )
        response = feedback.get_description()
        validate_text = "Ja, de melder is tevreden\nWaarom: my,\ntest,\nlist\nToelichting: extra_text\n" \
                        "Toestemming contact opnemen: Ja"
        self.assertEqual(response, validate_text)

        feedback = FeedbackFactory.create(
            is_satisfied=False,
            text="My Text",
            text_list=None,
            text_extra=None,
            allows_contact=False,
        )
        response = feedback.get_description()
        validate_text = "Nee, de melder is ontevreden\nWaarom: My Text\n" \
                        "Toestemming contact opnemen: Nee"
        self.assertEqual(response, validate_text)

    def test_get_frontend_positive_feedback_url(self):
        test_frontend_urls = ['https://acc.meldingen.amsterdam.nl', 'https://meldingen.amsterdam.nl',
                              'https://random.net', ]
        for test_frontend_url in test_frontend_urls:
            with override_settings(FRONTEND_URL=test_frontend_url):
                self.assertEqual(f'{test_frontend_url}/kto/ja/{self.feedback.token}',
                                 self.feedback.get_frontend_positive_feedback_url())

    def test_get_frontend_negative_feedback_url(self):
        test_frontend_urls = ['https://acc.meldingen.amsterdam.nl', 'https://meldingen.amsterdam.nl',
                              'https://random.net', ]
        for test_frontend_url in test_frontend_urls:
            with override_settings(FRONTEND_URL=test_frontend_url):
                self.assertEqual(f'{test_frontend_url}/kto/nee/{self.feedback.token}',
                                 self.feedback.get_frontend_negative_feedback_url())
