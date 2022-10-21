# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

# Note: also see tests for underlying service


class TestCleanUpReactionRequested(TestCase):
    @patch(
        'signals.apps.questionnaires.management.commands.clean_up_reaction_requested.clean_up_reaction_request',
        autospec=True
    )
    def test_command(self, patched_function):
        patched_function.return_value = 5
        buffer = StringIO()
        call_command('clean_up_reaction_requested', stdout=buffer)
        patched_function.assert_called_once_with()

        output = buffer.getvalue()
        self.assertIn('Updated 5 signals.', output)
