# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings


class TestDeleteSignalsBase(TestCase):
    """
    Test the delete_signals management command.

    - Test if the command will not run when DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED is False
    - Test if the required parameters are given
    - Test if the required parameters are valid
    """

    def setUp(self):
        self.feature_flags = settings.FEATURE_FLAGS
        if 'DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED' not in self.feature_flags:
            self.feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = False

    def test_call_feature_disabled(self):
        feature_flags = self.feature_flags
        feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = False

        buffer = StringIO()
        err_buffer = StringIO()
        with override_settings(FEATURE_FLAGS=feature_flags):
            call_command('delete_signals', 'a', '365', stdout=buffer, stderr=err_buffer)
        output = buffer.getvalue()
        err_output = err_buffer.getvalue()

        self.assertEqual(output, '')
        self.assertIn('Feature flag "DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED" is not enabled', err_output)

    def test_call_with_invalid_parameters(self):
        feature_flags = self.feature_flags
        feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        buffer = StringIO()
        err_buffer = StringIO()
        with override_settings(FEATURE_FLAGS=feature_flags):
            call_command('delete_signals', 'x', '100', stdout=buffer, stderr=err_buffer)
        output = buffer.getvalue()
        err_output = err_buffer.getvalue()

        self.assertEqual(output, '')
        self.assertIn('Invalid state(s) provided must be one of "o, a"', err_output)

        buffer = StringIO()
        err_buffer = StringIO()
        with override_settings(FEATURE_FLAGS=feature_flags):
            call_command('delete_signals', 'a', '100', stdout=buffer, stderr=err_buffer)
        output = buffer.getvalue()
        err_output = err_buffer.getvalue()

        self.assertEqual(output, '')
        self.assertIn('Invalid days provided must be at least 365', err_output)

    def test_call_with_valid_parameters(self):
        feature_flags = self.feature_flags
        feature_flags['DELETE_SIGNALS_IN_STATE_X_AFTER_PERIOD_Y_ENABLED'] = True

        buffer = StringIO()
        err_buffer = StringIO()
        with override_settings(FEATURE_FLAGS=feature_flags):
            call_command('delete_signals', 'o', '365', stdout=buffer, stderr=err_buffer)
        err_output = err_buffer.getvalue()

        self.assertEqual(err_output, '')
