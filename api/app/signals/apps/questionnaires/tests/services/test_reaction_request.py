# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils.timezone import now
from freezegun import freeze_time

from signals.apps.questionnaires.exceptions import SessionNotFrozen, WrongFlow, WrongState
from signals.apps.questionnaires.factories import AnswerFactory, QuestionFactory, SessionFactory
from signals.apps.questionnaires.models import Question, Questionnaire
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
        self.assertEqual(reaction_url, f'http://dummy_link/incident/reactie/{session.uuid}')

    def test_create_session(self):
        session = ReactionRequestService.create_session(self.signal_reaction_requested)
        self.assertEqual(session.questionnaire.first_question.label, self.signal_reaction_requested.status.text)
        self.assertEqual(session.questionnaire.flow, Questionnaire.REACTION_REQUEST)

    def test_create_session_wrong_state(self):
        with self.assertRaises(WrongState):
            ReactionRequestService.create_session(self.signal)

    def test_handle_frozen_session_REACTION_REQUEST_not_frozen(self):
        session = SessionFactory.create(
            questionnaire__flow=Questionnaire.REACTION_REQUEST, frozen=False, _signal=self.signal_reaction_requested)
        with self.assertRaises(SessionNotFrozen):
            ReactionRequestService.handle_frozen_session_REACTION_REQUEST(session)

    def test_handle_frozen_session_REACTION_REQUEST_wrong_flow(self):
        session = SessionFactory.create(
            questionnaire__flow=Questionnaire.EXTRA_PROPERTIES, frozen=True, _signal=self.signal_reaction_requested)
        with self.assertRaises(WrongFlow):
            ReactionRequestService.handle_frozen_session_REACTION_REQUEST(session)

    def test_handle_frozen_session_REACTION_REQUEST(self):
        question = QuestionFactory.create(
            field_type='plain_text', label='Is het goed weer?', short_label='Goed weer?')
        session = SessionFactory.create(
            questionnaire__flow=Questionnaire.REACTION_REQUEST,
            questionnaire__first_question=question,
            frozen=True,
            _signal=self.signal_reaction_requested
        )
        answer = AnswerFactory(session=session, payload='Het antwoord!')

        ReactionRequestService.handle_frozen_session_REACTION_REQUEST(session)

        self.signal_reaction_requested.refresh_from_db()
        self.assertEqual(self.signal_reaction_requested.status.state, workflow.REACTIE_ONTVANGEN)
        self.assertEqual(self.signal_reaction_requested.status.text, answer.payload)

    def test_handle_frozen_session_on_commit_triggered(self):
        question = QuestionFactory.create(
            field_type='plain_text', label='Is het goed weer?', short_label='Goed weer?')
        session = SessionFactory.create(
            questionnaire__flow=Questionnaire.REACTION_REQUEST,
            questionnaire__first_question=question,
            frozen=False,
            _signal=self.signal_reaction_requested
        )
        answer = AnswerFactory(session=session, payload='Het antwoord!')

        submit_question = Question.objects.get_by_reference('submit')

        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            QuestionnairesService.create_answer(
                answer_payload=None,
                question=submit_question,
                questionnaire=session.questionnaire,
                session=session
            )

        self.assertEqual(len(callbacks), 1)
        callbacks[0]()

        self.signal_reaction_requested.refresh_from_db()
        self.assertEqual(self.signal_reaction_requested.status.state, workflow.REACTIE_ONTVANGEN)
        self.assertEqual(self.signal_reaction_requested.status.text, answer.payload)

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
