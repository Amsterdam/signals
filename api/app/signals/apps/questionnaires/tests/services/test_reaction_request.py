# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from unittest import mock

from django.test import TestCase

from signals.apps.questionnaires.exceptions import WrongState
from signals.apps.questionnaires.factories import SessionFactory
from signals.apps.questionnaires.models import Questionnaire
from signals.apps.questionnaires.services import QuestionnairesService, ReactionRequestService
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory


class TestReactionRequestService(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create(status__state=workflow.GEMELD)
        self.signal_reaction_requested = SignalFactory.create(
            status__state=workflow.REACTIE_GEVRAAGD,
            status__text='Omschrijf uw probleem.',
        )

    @mock.patch.dict('os.environ', {'ENVIRONMENT': 'LOCAL'}, clear=True)
    def test_get_reaction_url(self):
        session = SessionFactory.create()
        reaction_url = ReactionRequestService.get_reaction_url(session)
        self.assertEqual(reaction_url, f'http://dummy_link/reactie_gevraagd/{session.uuid}')

    def test_create_session(self):
        session = ReactionRequestService.create_session(self.signal_reaction_requested)
        self.assertEqual(session.questionnaire.first_question.label, self.signal_reaction_requested.status.text)
        self.assertEqual(session.questionnaire.flow, Questionnaire.REACTION_REQUEST)

    def test_create_session_wrong_state(self):
        with self.assertRaises(WrongState):
            ReactionRequestService.create_session(self.signal)

    @mock.patch('signals.apps.questionnaires.services.questionnaires.session_frozen')
    def test_submit_session(self, patched_signal):
        session = ReactionRequestService.create_session(self.signal_reaction_requested)

        questionnaire = session.questionnaire
        question = questionnaire.first_question
        answer_str = 'De zon schijnt te vel.'

        answer = QuestionnairesService.create_answer(
            answer_payload=answer_str, question=question, questionnaire=questionnaire, session=session)
        next_question = QuestionnairesService.get_next_question(answer, question)
        self.assertEqual(next_question.ref, 'submit')

        with self.captureOnCommitCallbacks(execute=True):
            QuestionnairesService.create_answer(
                answer_payload=None, question=next_question, questionnaire=questionnaire, session=session)

        self.assertTrue(session.frozen)
        self.assertEqual(session.questionnaire.flow, Questionnaire.REACTION_REQUEST)
        patched_signal.send_robust.assert_called_once_with(sender=QuestionnairesService, session=session)
