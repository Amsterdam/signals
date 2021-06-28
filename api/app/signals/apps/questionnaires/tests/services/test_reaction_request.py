# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils.timezone import now
from freezegun import freeze_time

from signals.apps.questionnaires.exceptions import WrongState
from signals.apps.questionnaires.factories import SessionFactory
from signals.apps.questionnaires.models import Questionnaire
from signals.apps.questionnaires.services import QuestionnairesService, ReactionRequestService
from signals.apps.questionnaires.services.reaction_request import REACTION_REQUEST_DAYS_OPEN
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory
from signals.apps.signals.models import Signal


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
    def test_submit_session_signal_fired(self, patched_signal):
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

    @mock.patch('signals.apps.questionnaires.signal_receivers.tasks')
    def test_submit_session_signal_received(self, patched_task):
        # TODO: rewrite to omit the sending part, just trigger the appropriate Django signal
        session = ReactionRequestService.create_session(self.signal_reaction_requested)

        questionnaire = session.questionnaire
        question = questionnaire.first_question
        answer_str = 'De zon schijnt te vel.'

        answer = QuestionnairesService.create_answer(
            answer_payload=answer_str, question=question, questionnaire=questionnaire, session=session)
        next_question = QuestionnairesService.get_next_question(answer, question)
        self.assertEqual(next_question.ref, 'submit')

        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            QuestionnairesService.create_answer(
                answer_payload=None, question=next_question, questionnaire=questionnaire, session=session)

        self.assertEqual(len(callbacks), 1)
        callbacks[0]()

        patched_task.update_status_reactie_ontvangen.assert_called_once_with(pk=session.pk)

    def test_clean_up_reaction_request(self):
        # Make sure that the Signals created in setUp() method do not affect
        # this test:
        status = StatusFactory.create(text='xyz', state=workflow.BEHANDELING, _signal=self.signal_reaction_requested)
        self.signal_reaction_requested.status = status
        self.signal_reaction_requested.save()

        with freeze_time(now() - timedelta(days=2 * REACTION_REQUEST_DAYS_OPEN)):
            # Five signals that were in state REACTIE_GEVRAAGD and too old to
            # still receive an update.
            SignalFactory.create_batch(5, status__state=workflow.REACTIE_GEVRAAGD)

        with freeze_time(now() - timedelta(days=REACTION_REQUEST_DAYS_OPEN // 2)):
            # Five signals that were in state REACTIE_GEVRAAGD and may still
            # get an update.
            SignalFactory.create_batch(5, status__state=workflow.REACTIE_GEVRAAGD)

        self.assertEqual(Signal.objects.count(), 12)
        n_updated = ReactionRequestService.clean_up_reaction_request()

        self.assertEqual(n_updated, 5)
        reactie_gevraagd = Signal.objects.filter(status__state=workflow.REACTIE_GEVRAAGD)
        reactie_ontvangen = Signal.objects.filter(status__state=workflow.REACTIE_ONTVANGEN)

        self.assertEqual(reactie_gevraagd.count(), 5)
        self.assertEqual(reactie_ontvangen.count(), 5)
