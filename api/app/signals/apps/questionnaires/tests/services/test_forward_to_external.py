# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from datetime import timedelta

from django.conf import settings
from django.test import TestCase
from django.utils.timezone import now
from freezegun import freeze_time

from signals.apps.questionnaires.exceptions import CannotFreeze, MissingEmail, WrongFlow, WrongState
from signals.apps.questionnaires.factories import AnswerFactory
from signals.apps.questionnaires.services.forward_to_external import (
    clean_up_forward_to_external,
    create_session_for_forward_to_external,
    FORWARD_TO_EXTERNAL_DAYS_OPEN,
    ForwardToExternalSessionService,
    get_forward_to_external_url
)
from signals.apps.questionnaires.models import Edge, Questionnaire, Session
from signals.apps.questionnaires.services.utils import get_session_service
from signals.apps.signals.factories import SignalFactory, SignalFactoryValidLocation, StatusFactory
from signals.apps.signals.models import Signal, Status
from signals.apps.signals.workflow import (
    BEHANDELING,
    GEMELD,
    DOORZETTEN_NAAR_EXTERN,
    VERZOEK_TOT_AFHANDELING
)

# TODO:
# - test answering the photo upload question
# - test that the various deadlines are correctly set on created session


class TestCreateSessionForForwardToExternal(TestCase):
    def setUp(self):
        self.signal = SignalFactoryValidLocation.create()
        status_text = 'Kunt u de lantaarn vervangen?'
        new_status = Status.objects.create(
            _signal_id=self.signal.id, state=DOORZETTEN_NAAR_EXTERN, text=status_text, email_override='a@example.com')
        self.signal.status = new_status
        self.signal.save()

    def test_create_session_for_forward_to_external_wrong_state(self):
        signal = SignalFactory.create(status__state=GEMELD)
        with self.assertRaises(WrongState):
            create_session_for_forward_to_external(signal)

    def test_create_session_for_forward_to_external_email_override_none(self):
        signal = SignalFactory.create(status__state=DOORZETTEN_NAAR_EXTERN, status__email_override=None)
        with self.assertRaises(MissingEmail):
            create_session_for_forward_to_external(signal)

    def test_create_session_for_forward_to_external(self):
        # Check basic characteristics of created Questions, QuestionGraph, Questionnaire, and Session
        session = create_session_for_forward_to_external(self.signal)
        self.assertIsInstance(session, Session)
        self.assertEqual(session.questionnaire.flow, Questionnaire.FORWARD_TO_EXTERNAL)
        self.assertEqual(session.status.email_override, 'a@example.com')

        # Check explanatory text based new Signal status
        explanation = session.questionnaire.explanation
        self.assertEqual(explanation.sections.count(), 2)  # change when copying attachments is implemented

        sections = explanation.sections.all()
        self.assertEqual(sections[0].header, 'De melding')
        self.assertIn(self.signal.get_id_display(), sections[0].text)

        self.assertEqual(sections[1].header, 'Omschrijving')
        self.assertEqual(sections[1].text, self.signal.status.text)

        # Check question graph structure
        graph = session.questionnaire.graph
        edges = Edge.objects.filter(graph=graph)
        self.assertEqual(edges.count(), 1)

        first_question = graph.first_question
        self.assertEqual(first_question.short_label,'Reactie na afhandeling')

        edge_to_second_question = Edge.objects.filter(graph=graph, question=first_question).first()
        second_question = edge_to_second_question.next_question
        self.assertEqual(second_question.short_label, "Foto's toevoegen")


class TestGetForwardToExternalUrl(TestCase):
    def test_get_forward_to_external_url(self):
        signal = SignalFactory.create(status__state=DOORZETTEN_NAAR_EXTERN, status__email_override='a@example.com')
        session = create_session_for_forward_to_external(signal)

        url = f'{settings.FRONTEND_URL}/incident/extern/{session.uuid}'
        self.assertEqual(get_forward_to_external_url(session), url)


class TestForwardToExternalSessionService(TestCase):
    def setUp(self):
        self.signal = SignalFactoryValidLocation.create()
        self.status_text = 'Kunt u de lantaarn vervangen?'
        new_status = Status.objects.create(
            _signal_id=self.signal.id, state=DOORZETTEN_NAAR_EXTERN, text=self.status_text, email_override='a@example.com')
        self.signal.status = new_status
        self.signal.save()

        self.session = create_session_for_forward_to_external(self.signal)  # see TestCreateSessionForForwardToExternal
        self.assertIsInstance(self.session, Session)

    def test_handle_frozen_session_FORWARD_TO_EXTERNAL_not_filled_out(self):
        service = get_session_service(self.session.uuid)
        self.assertIsInstance(service, ForwardToExternalSessionService)

        with self.assertRaises(CannotFreeze):
            service.freeze()

        # Using knowledge that only the first question is mandatory in FORWARD_TO_EXTERNAL flow questionnaire:
        AnswerFactory(session=self.session, payload='Lantaarn is gefixt!')

        service.refresh_from_db()
        service.freeze()
        self.session.refresh_from_db()
        self.assertEqual(self.session.frozen, True)

    def test_handle_frozen_session_FORWARD_TO_EXTERNAL_wrong_flow(self):
        service = get_session_service(self.session.uuid)
        self.assertIsInstance(service, ForwardToExternalSessionService)

        # Using knowledge that only the first question is mandatory in FORWARD_TO_EXTERNAL flow questionnaire:
        AnswerFactory(session=self.session, payload='Lantaarn is gefixt!')

        # Change Questionnaire flow from Questionnaire.FORWARD_TO_EXTERNAL
        self.session.questionnaire.flow = Questionnaire.EXTRA_PROPERTIES
        self.session.questionnaire.save()
        service.refresh_from_db()

        self.assertEqual(service.session.questionnaire.flow, Questionnaire.EXTRA_PROPERTIES)
        with self.assertRaises(WrongFlow):
            service.freeze()

        # Using knowledge that only the first question is mandatory in FORWARD_TO_EXTERNAL flow questionnaire:
        AnswerFactory(session=self.session, payload='Lantaarn is gefixt!')

    def test_handle_frozen_session_FORWARD_TO_EXTERNAL(self):
        service = get_session_service(self.session.uuid)
        self.assertIsInstance(service, ForwardToExternalSessionService)

        # Using knowledge that only the first question is mandatory in FORWARD_TO_EXTERNAL flow:
        answer = AnswerFactory(session=self.session, payload='Lantaarn is gefixt!')

        service.refresh_from_db()
        service.freeze()

        self.signal.refresh_from_db()
        self.assertEqual(self.signal.status.state, VERZOEK_TOT_AFHANDELING)
        self.assertEqual(self.signal.status.text, f'Toelichting door behandelaar (a@example.com): {answer.payload}')


class TestCleanUpForwardToExternal(TestCase):
    def test_clean_up_forward_to_external_from_DOORZETTEN_NAAR_EXTERN(self):
        with freeze_time(now() - timedelta(days=2 * FORWARD_TO_EXTERNAL_DAYS_OPEN)):
            # Five signals that were in state DOORZETTEN_NAAR_EXTERN and too old to
            # still receive an update.
            signals = SignalFactory.create_batch(
                5, status__state=DOORZETTEN_NAAR_EXTERN, status__email_override='a@example.com')
            for signal in signals:
                create_session_for_forward_to_external(signal)

        with freeze_time(now() - timedelta(days=FORWARD_TO_EXTERNAL_DAYS_OPEN // 2)):
            # Five signals that were in state DOORZETTEN_NAAR_EXTERN and may still
            # get an update.
            SignalFactory.create_batch(
                5, status__state=DOORZETTEN_NAAR_EXTERN, status__email_override='a@example.com')
            for signal in signals:
                create_session_for_forward_to_external(signal)

        self.assertEqual(Signal.objects.count(), 10)
        n_updated = clean_up_forward_to_external()

        self.assertEqual(n_updated, 5)
        closed = Signal.objects.filter(status__state=DOORZETTEN_NAAR_EXTERN)
        still_open = Signal.objects.filter(status__state=VERZOEK_TOT_AFHANDELING)

        self.assertEqual(closed.count(), 5)
        self.assertEqual(still_open.count(), 5)

        self.assertEqual(Session.objects.count(), 10)
        self.assertEqual(Session.objects.filter(invalidated=True).count(), 5)

    def test_clean_up_forward_to_external_not_from_DOORZETTEN_NAAR_EXTERN(self):
        with freeze_time(now() - timedelta(days=2 * FORWARD_TO_EXTERNAL_DAYS_OPEN)):
            # Five signals that were in state DOORZETTEN_NAAR_EXTERN and too old to
            # still receive an update.
            signal = SignalFactory.create(status__state=DOORZETTEN_NAAR_EXTERN, status__email_override='a@example.com')
            create_session_for_forward_to_external(signal)
            new_status = StatusFactory.create(_signal=signal)
            signal.status = new_status
            signal.save()

        with freeze_time(now() - timedelta(days=FORWARD_TO_EXTERNAL_DAYS_OPEN // 2)):
            # Five signals that were in state DOORZETTEN_NAAR_EXTERN and may still
            # get an update.
            signal = SignalFactory.create(status__state=DOORZETTEN_NAAR_EXTERN, status__email_override='a@example.com')
            create_session_for_forward_to_external(signal)
            new_status = StatusFactory.create(_signal=signal)
            signal.status = new_status
            signal.save()

        self.assertEqual(Signal.objects.count(), 2)
        n_updated = clean_up_forward_to_external()

        self.assertEqual(n_updated, 1)
        self.assertEqual(Signal.objects.filter(status__state=GEMELD).count(), 2)  # we want no state changes

        self.assertEqual(Session.objects.count(), 2)
        self.assertEqual(Session.objects.filter(invalidated=True).count(), 1)
