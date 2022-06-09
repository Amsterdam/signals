# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam


from django.test import TestCase

from signals.apps.feedback.serializers import FeedbackSerializer


class TestFeedbackSerializer(TestCase):

    def setUp(self):
        self.data = {
            'is_satisfied': False,
            'allows_contact': True,
            'text_extra': 'fake_text_extra'
        }

    def test_validate_text(self):
        self.data['text'] = 'fake_text'

        serializer = FeedbackSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())

    def test_validate_text_list(self):
        self.data['text_list'] = ['fake_text']

        serializer = FeedbackSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())

    def test_validate_text_and_list(self):
        self.data['text'] = 'fake_text'
        self.data['text_list'] = ['fake_text']

        serializer = FeedbackSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())

    def test_validate_missing_both(self):
        serializer = FeedbackSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        err = serializer.errors
        self.assertIn('non_field_errors', err)
        self.assertEqual(str(err['non_field_errors'][0]),
                         'Either text or text_list must be filled in')
        self.assertTrue(len(err['non_field_errors']) == 1)
