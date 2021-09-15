# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils.timezone import now
from freezegun import freeze_time

from signals.apps.questionnaires.exceptions import WrongFlow, WrongState
from signals.apps.questionnaires.factories import (
    AnswerFactory,
    QuestionFactory,
    QuestionGraphFactory,
    SessionFactory
)
from signals.apps.questionnaires.models import Questionnaire
from signals.apps.questionnaires.services.reaction_request import (
    REACTION_REQUEST_DAYS_OPEN,
    ReactionRequestSessionService,
    clean_up_reaction_request,
    create_session_for_reaction_request,
    get_reaction_url
)
from signals.apps.questionnaires.services.utils import get_session_service
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory
from signals.apps.signals.models import Signal


class TestReactionRequestSessionService(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create(status__state=workflow.GEMELD)
        self.signal_reaction_requested = SignalFactory.create(
            status__state=workflow.REACTIE_GEVRAAGD,
            status__text='Omschrijf uw probleem.',
        )

    @mock.patch.dict('os.environ', {'ENVIRONMENT': 'LOCAL'}, clear=True)
    def test_get_reaction_url(self):
        session = SessionFactory.create()
        reaction_url = get_reaction_url(session)
        self.assertEqual(reaction_url, f'http://dummy_link/incident/reactie/{session.uuid}')

    def test_create_session(self):
        session = create_session_for_reaction_request(self.signal_reaction_requested)
        self.assertEqual(session.questionnaire.graph.first_question.label, self.signal_reaction_requested.status.text)
        self.assertEqual(session.questionnaire.flow, Questionnaire.REACTION_REQUEST)

    def test_create_session_wrong_state(self):
        with self.assertRaises(WrongState):
            create_session_for_reaction_request(self.signal)

    def test_handle_frozen_session_REACTION_REQUEST_wrong_flow(self):
        session = SessionFactory.create(
            questionnaire__flow=Questionnaire.REACTION_REQUEST, frozen=True, _signal=self.signal_reaction_requested)
        AnswerFactory(session=session, payload='Het antwoord!')

        service = get_session_service(session.uuid)
        self.assertIsInstance(service, ReactionRequestSessionService)
        session.questionnaire.flow = Questionnaire.EXTRA_PROPERTIES
        session.questionnaire.save()

        service.load_data()
        self.assertEqual(service.session.questionnaire.flow, Questionnaire.EXTRA_PROPERTIES)
        with self.assertRaises(WrongFlow):  # Deal with CannotFreeze
            service.freeze()

    def test_handle_frozen_session_REACTION_REQUEST(self):
        question = QuestionFactory.create(
            field_type='plain_text',
            label='Is het goed weer?',
            short_label='Goed weer?',
            analysis_key='reaction',
        )
        graph = QuestionGraphFactory.create(name='Reactie gevraagd.', first_question=question)
        session = SessionFactory.create(
            questionnaire__flow=Questionnaire.REACTION_REQUEST,
            questionnaire__graph=graph,
            frozen=True,
            _signal=self.signal_reaction_requested
        )
        answer = AnswerFactory(session=session, payload='Het antwoord!')

        service = get_session_service(session.uuid)
        self.assertIsInstance(service, ReactionRequestSessionService)
        service.freeze()

        self.signal_reaction_requested.refresh_from_db()
        self.assertEqual(self.signal_reaction_requested.status.state, workflow.REACTIE_ONTVANGEN)
        self.assertEqual(self.signal_reaction_requested.status.text, answer.payload)

    def test_handle_frozen_session_on_commit_triggered(self):
        question = QuestionFactory.create(
            field_type='plain_text',
            label='Is het goed weer?',
            short_label='Goed weer?',
            analysis_key='reaction',
        )
        graph = QuestionGraphFactory.create(name='Reactie gevraagd.', first_question=question)
        session = SessionFactory.create(
            questionnaire__flow=Questionnaire.REACTION_REQUEST,
            questionnaire__graph=graph,
            frozen=False,
            _signal=self.signal_reaction_requested
        )
        answer = AnswerFactory(session=session, payload='Het antwoord!')

        service = get_session_service(session.uuid)
        self.assertIsInstance(service, ReactionRequestSessionService)
        service.freeze()

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
        n_updated = clean_up_reaction_request()

        self.assertEqual(n_updated, 5)
        reactie_gevraagd = Signal.objects.filter(status__state=workflow.REACTIE_GEVRAAGD)
        reactie_ontvangen = Signal.objects.filter(status__state=workflow.REACTIE_ONTVANGEN)

        self.assertEqual(reactie_gevraagd.count(), 5)
        self.assertEqual(reactie_ontvangen.count(), 5)
