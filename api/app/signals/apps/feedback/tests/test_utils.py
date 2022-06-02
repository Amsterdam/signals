# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam

from django.test import TestCase

from signals.apps.feedback.utils import validate_answers, merge_texts


class TestFeedbackUtils(TestCase):

    _REOPEN_TEXT = "Er is niets met mijn melding gedaan"
    _REOPEN_TEXT_2 = "Ik voel mij niet serieus genomen door de gemeente"
    _STAY_CLOSED_TEXT = "De behandeling duurde te lang"
    _STAY_CLOSED_TEXT_2 = "Het contact over de afhandeling was slecht"

    def test_validate_answers_text_list_only_reopen(self):
        """
        text_list only when an reopens when unhappy string
        """
        data = {'text_list': [self._REOPEN_TEXT]}

        self.assertTrue(validate_answers(data))

    def test_validate_answers_text_list_only_stay_closed(self):
        """
        text_list only when and stay closed
        """
        data = {'text_list': [self._STAY_CLOSED_TEXT]}

        self.assertFalse(validate_answers(data))

    def test_validate_answers_text_list_reopen_and_close(self):
        """
        text_list with multiple anwsers and only triggers reopen it should true to reopen the signal
        """
        data = {'text_list': [self._REOPEN_TEXT, self._STAY_CLOSED_TEXT]}
        self.assertTrue(validate_answers(data))

    def test_validate_answers_text_list_custom_text(self):
        """
        text_list with a custom text should always return true to reopen the signal
        """
        data = {'text_list': ["SOME CUSTOMER TEXT"]}
        self.assertTrue(validate_answers(data))

    def test_validate_answers_text_list_multiple_reopen(self):
        """
        if text_list has multiple reopen texts
        """
        data = {
            'text_list': [self._REOPEN_TEXT, self._REOPEN_TEXT_2]}
        self.assertTrue(validate_answers(data))

    def test_validate_answers_text_list_multiple_stay_closed(self):
        """
        if text_list has multiple stay closed texts
        """
        data = {'text_list': [self._STAY_CLOSED_TEXT, self._STAY_CLOSED_TEXT_2]}
        self.assertFalse(validate_answers(data))

    def test_validate_answers_text_list_multiple_stay_mixed(self):
        """
        if text_list has closed and reopen mixed
        """
        data = {'text_list': [self._STAY_CLOSED_TEXT, self._STAY_CLOSED_TEXT_2, self._REOPEN_TEXT_2]}
        self.assertTrue(validate_answers(data))

    def test_validate_answers_text_list_multiple_closed_with_custom(self):
        """
        if text_list has a custom text in it
        """
        data = {'text_list': [self._STAY_CLOSED_TEXT, self._STAY_CLOSED_TEXT_2, "some reporter text"]}
        self.assertTrue(validate_answers(data))

    def test_validate_answers_duplicate(self):
        """
        Create a check to see that duplicate messages are not seen as custom texts because of a list diff.
        and keep the signal Close with duplicate closed texts
        """
        data = {'text_list': [self._STAY_CLOSED_TEXT,
                              self._STAY_CLOSED_TEXT,
                              self._STAY_CLOSED_TEXT]}

        self.assertFalse(validate_answers(data))

    def test_merge_text_only_text(self):
        """
        Only text and convert it to text_list
        """
        data = {'text': 'test'}

        data = merge_texts(data)
        self.assertNotIn('text', data)
        self.assertIn('test', data['text_list'])

    def test_merge_text_only_text_list(self):
        """
        Only text and convert it to text_list
        """
        data = {'text_list': ['test', 'a', 'text']}

        data = merge_texts(data)
        self.assertNotIn('text', data)
        self.assertEqual(['test', 'a', 'text'], data['text_list'])

    def test_merge_text_text_and_list(self):
        """
        Only text and convert it to text_list
        """
        data = {
            'text': 'my_text',
            'text_list': ['test', 'a', 'text']
        }

        data = merge_texts(data)
        self.assertNotIn('text', data)
        self.assertEqual(['test', 'a', 'text', 'my_text'], data['text_list'])
