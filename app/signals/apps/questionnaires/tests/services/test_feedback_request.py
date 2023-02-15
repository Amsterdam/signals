# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import datetime, timedelta

from django.conf import settings
from django.test import TestCase
from django.utils.timezone import make_aware
from freezegun import freeze_time

from signals.apps.feedback.factories import StandardAnswerFactory
from signals.apps.feedback.models import Feedback, StandardAnswer
from signals.apps.questionnaires.app_settings import FEEDBACK_REQUEST_DAYS_OPEN
from signals.apps.questionnaires.exceptions import WrongState
from signals.apps.questionnaires.factories import SessionFactory
from signals.apps.questionnaires.models import Question, Session
from signals.apps.questionnaires.services import FeedbackRequestSessionService
from signals.apps.questionnaires.services.feedback_request import (
    create_session_for_feedback_request,
    get_feedback_urls
)
from signals.apps.questionnaires.services.utils import get_session_service
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory


class TestFeedbackRequestSessionService(TestCase):
    def setUp(self):
        self.now = make_aware(datetime(2021, 8, 12, 12, 0, 0))

        StandardAnswer.objects.all().delete()  # Production system has Standard answers via migration, remove for test
        StandardAnswerFactory.create(is_visible=True, text='all good', is_satisfied=True, reopens_when_unhappy=False)
        StandardAnswerFactory.create(is_visible=False, text='old', is_satisfied=True, reopens_when_unhappy=False)
        StandardAnswerFactory.create(is_visible=True, text='not good', is_satisfied=False, reopens_when_unhappy=False)
        StandardAnswerFactory.create(is_visible=True, text='never good', is_satisfied=False, reopens_when_unhappy=True)

    def test_get_feedback_urls(self):
        session = SessionFactory.create()
        pos_url, neg_url = get_feedback_urls(session)

        self.assertEqual(f'{settings.FRONTEND_URL}/feedback/ja/{session.uuid}', pos_url)
        self.assertEqual(f'{settings.FRONTEND_URL}/feedback/nee/{session.uuid}', neg_url)

    def test_create_session_wrong_state(self):
        signal = SignalFactory.create(status__state=workflow.BEHANDELING)

        with self.assertRaises(WrongState):
            create_session_for_feedback_request(signal)

    def test_create_session(self):
        with freeze_time(self.now):
            signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
            session = create_session_for_feedback_request(signal)

        dt = (session.submit_before - self.now)
        self.assertEqual(dt, timedelta(days=FEEDBACK_REQUEST_DAYS_OPEN))
        self.assertEqual(session._signal, signal)

    def test_questionnaire(self):
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        session = create_session_for_feedback_request(signal)
        questionnaire = session.questionnaire
        graph = questionnaire.graph

        self.assertEqual(questionnaire.first_question.analysis_key, 'satisfied')
        # TODO: use QuestionGraphService:
        all_questions = Question.objects.get_from_question_graph(graph)
        self.assertEqual(all_questions.count(), 5)
        # TODO: use QuestionGraphService:
        reachable_questions = Question.objects.get_reachable_from_question_graph(graph)
        self.assertEqual(reachable_questions.count(), 5)

    def test_create_two_questionnaires(self):
        # We cannot re-use Question.key, this test demonstrates the problem
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        session_1 = create_session_for_feedback_request(signal)
        session_2 = create_session_for_feedback_request(signal)

        self.assertIsInstance(session_1, Session)
        self.assertIsInstance(session_2, Session)

    def test_fill_out_questionnaire_satisfied(self):
        # Check predefined questionnaire structure, then fill out the questionnaire.
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        session = create_session_for_feedback_request(signal)
        service = get_session_service(session)
        self.assertIsInstance(service, FeedbackRequestSessionService)
        service.refresh_from_db()

        question_1 = session.questionnaire.graph.first_question
        self.assertEqual(question_1.analysis_key, 'satisfied')
        answer_1 = service.create_answer(True, question_1)

        question_2 = service.get_next_question(question_1, answer_1)
        self.assertEqual(question_2.analysis_key, 'reason_satisfied')

        # We re-use the feedback app for pre-defined answers (that will allow
        # management of this questionnaire as if it was still implemented by
        # the feedback).
        happy_standard_answer = StandardAnswer.objects.filter(
            is_visible=True, is_satisfied=True, reopens_when_unhappy=False).first()
        answer_2 = service.create_answer(happy_standard_answer.text, question_2)

        question_3 = service.get_next_question(question_2, answer_2)
        self.assertEqual(question_3.analysis_key, 'extra_info')
        answer_3 = service.create_answer('Dit is extra informatie', question_3)

        question_4 = service.get_next_question(question_3, answer_3)
        self.assertEqual(question_4.analysis_key, 'allows_contact')
        answer_4 = service.create_answer(True, question_4)

        question_5 = service.get_next_question(question_4, answer_4)
        self.assertIsNone(question_5, None)

    def test_fill_out_questionnaire_unsatisfied_with_reopen_requested(self):
        """
        Trigger a reopen request on Signal.
        """
        # -- set up our session and SessionService subclass
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        session = create_session_for_feedback_request(signal)
        service = get_session_service(session)
        self.assertIsInstance(service, FeedbackRequestSessionService)
        service.refresh_from_db()

        # -- complete questionnaire --
        question_1 = session.questionnaire.graph.first_question
        self.assertEqual(question_1.analysis_key, 'satisfied')
        answer_1 = service.create_answer(False, question_1)

        question_2 = service.get_next_question(question_1, answer_1)
        self.assertEqual(question_2.analysis_key, 'reason_unsatisfied')

        unhappy_standard_answer = StandardAnswer.objects.filter(
            is_visible=True, is_satisfied=False, reopens_when_unhappy=True).first()
        answer_2 = service.create_answer(unhappy_standard_answer.text, question_2)

        question_3 = service.get_next_question(question_2, answer_2)
        self.assertEqual(question_3.analysis_key, 'extra_info')
        answer_3 = service.create_answer('EXTRA INFO', question_3)

        question_4 = service.get_next_question(question_3, answer_3)
        self.assertEqual(question_4.analysis_key, 'allows_contact')
        answer_4 = service.create_answer(True, question_4)

        question_5 = service.get_next_question(question_4, answer_4)
        self.assertIsNone(question_5, None)

        # -- freeze session, access data, check actions after freeze
        service.refresh_from_db()
        service.freeze()
        self.assertEqual(Feedback.objects.count(), 1)
        signal.refresh_from_db()
        self.assertEqual(signal.status.state, workflow.VERZOEK_TOT_HEROPENEN)

        feedback = Feedback.objects.first()
        self.assertEqual(feedback.is_satisfied, False)
        self.assertEqual(feedback.text, unhappy_standard_answer.text)
        self.assertEqual(feedback.text_extra, 'EXTRA INFO')
        self.assertEqual(feedback.allows_contact, True)

    def test_fill_out_questionnaire_unsatisfied_without_reopen_requested(self):
        """
        Give feedback without triggering reopen request on Signal.
        """
        # -- set up our session and SessionService subclass
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        session = create_session_for_feedback_request(signal)
        service = get_session_service(session)
        self.assertIsInstance(service, FeedbackRequestSessionService)
        service.refresh_from_db()

        # -- complete questionnaire --
        question_1 = session.questionnaire.graph.first_question
        self.assertEqual(question_1.analysis_key, 'satisfied')
        answer_1 = service.create_answer(False, question_1)

        question_2 = service.get_next_question(question_1, answer_1)
        self.assertEqual(question_2.analysis_key, 'reason_unsatisfied')

        unhappy_standard_answer = StandardAnswer.objects.filter(
            is_visible=True, is_satisfied=False, reopens_when_unhappy=False).first()
        answer_2 = service.create_answer(unhappy_standard_answer.text, question_2)

        question_3 = service.get_next_question(question_2, answer_2)
        self.assertEqual(question_3.analysis_key, 'extra_info')
        answer_3 = service.create_answer('EXTRA INFO', question_3)

        question_4 = service.get_next_question(question_3, answer_3)
        self.assertEqual(question_4.analysis_key, 'allows_contact')
        answer_4 = service.create_answer(True, question_4)

        question_5 = service.get_next_question(question_4, answer_4)
        self.assertIsNone(question_5, None)

        # -- freeze session, access data, check actions after freeze
        service.refresh_from_db()
        service.freeze()
        self.assertEqual(Feedback.objects.count(), 1)
        signal.refresh_from_db()
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD)

        feedback = Feedback.objects.first()
        self.assertEqual(feedback.is_satisfied, False)
        self.assertEqual(feedback.text, unhappy_standard_answer.text)
        self.assertEqual(feedback.text_extra, 'EXTRA INFO')
        self.assertEqual(feedback.allows_contact, True)
