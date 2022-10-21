# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from unittest.mock import patch

from django.test import TestCase

from signals.apps.questionnaires.tasks import (
    clean_up_forward_to_external_task,
    clean_up_reaction_request_task
)


class TestCleanUpReactionRequestedTask(TestCase):
    @patch('signals.apps.questionnaires.tasks.clean_up_reaction_request', autospec=True)
    def test_task(self, patched_function):
        clean_up_reaction_request_task()
        patched_function.assert_called_once_with()


class TestCleanUpForwardToExternalTask(TestCase):
    @patch('signals.apps.questionnaires.tasks.clean_up_forward_to_external', autospec=True)
    def test_task(self, patched_function):
        clean_up_forward_to_external_task()
        patched_function.assert_called_once_with()
