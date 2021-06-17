# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from unittest import mock

from django.test import TestCase

from signals.apps.questionnaires.exceptions import WrongState
from signals.apps.questionnaires.factories import SessionFactory
from signals.apps.questionnaires.services import ReactionRequestService
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory


class TestReactionRequestService(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create(status__state=workflow.GEMELD)

    @mock.patch.dict('os.environ', {'ENVIRONMENT': 'LOCAL'}, clear=True)
    def test_get_reaction_url(self):
        session = SessionFactory.create()
        reaction_url = ReactionRequestService.get_reaction_url(session)
        self.assertEqual(reaction_url, f'http://dummy_link/reactie_gevraagd/{session.uuid}')

    def test_create_session(self):
        question_text = 'Omschrijf uw probleem.'
        status = StatusFactory(_signal=self.signal, state=workflow.REACTIE_GEVRAAGD, text=question_text)
        self.signal.status = status
        self.signal.save()
        self.signal.refresh_from_db()

        session = ReactionRequestService.create_session(self.signal)
        self.assertEqual(session.questionnaire.first_question.label, question_text)

    def test_create_session_wrong_state(self):
        with self.assertRaises(WrongState):
            ReactionRequestService.create_session(self.signal)
