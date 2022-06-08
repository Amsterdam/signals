# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase

from signals.apps.api.generics.mixins import convert_validation_error


class TestConvertValidationErrorFunction(TestCase):
    def test_error_with_message(self):
        error = DjangoValidationError('A message')

        self.assertTrue(hasattr(error, 'message'))
        self.assertTrue(hasattr(error, 'messages'))
        self.assertEqual(error.message, 'A message')
        self.assertEqual(error.messages[0], 'A message')

        converted_error = convert_validation_error(error)
        self.assertEqual(converted_error.detail[0], 'A message')

    def test_error_with_messages(self):
        error = DjangoValidationError([DjangoValidationError('First message'), DjangoValidationError('Second message')])

        self.assertFalse(hasattr(error, 'message'))
        self.assertTrue(hasattr(error, 'messages'))
        self.assertEqual(len(error.messages), 2)
        self.assertEqual(error.messages[0], 'First message')
        self.assertEqual(error.messages[1], 'Second message')

        converted_error = convert_validation_error(error)

        self.assertEqual(len(converted_error.detail), 2)
        self.assertEqual(converted_error.detail[0], 'First message')
        self.assertEqual(converted_error.detail[1], 'Second message')
