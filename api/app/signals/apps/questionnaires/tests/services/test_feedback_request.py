# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils.timezone import make_aware
from freezegun import freeze_time

from signals.apps.feedback.factories import FeedbackFactory, StandardAnswerFactory
from signals.apps.feedback.models import Feedback, StandardAnswer
from signals.apps.questionnaires.app_settings import FEEDBACK_REQUEST_DAYS_OPEN
from signals.apps.questionnaires.exceptions import WrongState
from signals.apps.questionnaires.factories import AnswerFactory, SessionFactory
from signals.apps.questionnaires.models import Edge, Question, Session
from signals.apps.questionnaires.services import FeedbackRequestService, QuestionnairesService
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory


class TestFeedbackRequestService(TestCase):
    def setUp(self):
        self.now = make_aware(datetime(2021, 8, 12, 12, 0, 0))

        StandardAnswerFactory.create(is_visible=True, text='all good', is_satisfied=True, reopens_when_unhappy=False)
        StandardAnswerFactory.create(is_visible=False, text='old', is_satisfied=True, reopens_when_unhappy=False)
        StandardAnswerFactory.create(is_visible=True, text='not good', is_satisfied=False, reopens_when_unhappy=False)
        StandardAnswerFactory.create(is_visible=True, text='never good', is_satisfied=False, reopens_when_unhappy=True)

    @patch('signals.apps.questionnaires.services.feedback_request.get_fe_application_location')
    def test_get_feedback_urls(self, patched):
        patched.return_value = 'http://dummy'
        session = SessionFactory.create()
        pos_url, neg_url = FeedbackRequestService.get_feedback_urls(session)

        self.assertEqual(f'http://dummy/feedback/ja/{session.uuid}', pos_url)
        self.assertEqual(f'http://dummy/feedback/nee/{session.uuid}', neg_url)

    def test_create_session_wrong_state(self):
        signal = SignalFactory.create(status__state=workflow.BEHANDELING)

        with self.assertRaises(WrongState):
            FeedbackRequestService.create_session(signal)

    def test_create_session(self):
        with freeze_time(self.now):
            signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
            session = FeedbackRequestService.create_session(signal)

        dt = (session.submit_before - self.now)
        self.assertEqual(dt, timedelta(days=FEEDBACK_REQUEST_DAYS_OPEN))
        self.assertEqual(session._signal, signal)

    def test_questionnaire(self):
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        session = FeedbackRequestService.create_session(signal)
        questionnaire = session.questionnaire
        graph = questionnaire.graph

        self.assertEqual(questionnaire.first_question.analysis_key, 'satisfied')
        all_questions = Question.objects.get_from_question_graph(graph)
        self.assertEqual(all_questions.count(), 5)
        reachable_questions = Question.objects.get_reachable_from_question_graph(graph)
        self.assertEqual(reachable_questions.count(), 5)

    def test_create_two_questionnaires(self):
        # We cannot re-use Question.key, this test demonstrates the problem
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        session_1 = FeedbackRequestService.create_session(signal)
        session_2 = FeedbackRequestService.create_session(signal)

        self.assertIsInstance(session_1, Session)
        self.assertIsInstance(session_2, Session)

    def test_fill_out_questionnaire_satisfied(self):
        # Check predefined questionnaire structure, then fill out the questionnaire.
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        session = FeedbackRequestService.create_session(signal)
        questionnaire = session.questionnaire
        graph = questionnaire.graph
        question_1 = questionnaire.graph.first_question
        self.assertEqual(question_1.analysis_key, 'satisfied')

        answer_1 = QuestionnairesService.create_answer(True, question_1, questionnaire, session=session)
        question_2 = QuestionnairesService.get_next_question(answer_1.payload, question_1, graph)
        self.assertEqual(question_2.analysis_key, 'reason_satisfied')

        # We re-use the feedback app for pre-defined answers (that will allow
        # management of this questionnaire as if it was still implemented by
        # the feedback).
        happy_standard_answer = StandardAnswer.objects.filter(
            is_visible=True, is_satisfied=True, reopens_when_unhappy=False).first()

        answer_2 = QuestionnairesService.create_answer(
            happy_standard_answer.text, question_2, questionnaire, session=session)
        question_3 = QuestionnairesService.get_next_question(answer_2.payload, question_2, graph)
        self.assertEqual(question_3.analysis_key, 'extra_info')

        answer_3 = QuestionnairesService.create_answer(
            'Dit is extra informatie', question_3, questionnaire, session=session)
        question_4 = QuestionnairesService.get_next_question(answer_3.payload, question_3, graph)
        self.assertEqual(question_4.analysis_key, 'allows_contact')

        answer_4 = QuestionnairesService.create_answer(True, question_4, questionnaire, session=session)
        question_5 = QuestionnairesService.get_next_question(answer_4.payload, question_4, graph)
        self.assertIsNone(question_5, None)

    def test_fill_out_questionnaire_unsatisfied(self):
        # Check predefined questionnaire structure, then fill out the questionnaire.
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        session = FeedbackRequestService.create_session(signal)
        questionnaire = session.questionnaire
        graph = questionnaire.graph
        question_1 = questionnaire.graph.first_question
        self.assertEqual(question_1.analysis_key, 'satisfied')

        answer_1 = QuestionnairesService.create_answer(False, question_1, questionnaire, session=session)
        question_2 = QuestionnairesService.get_next_question(answer_1.payload, question_1, graph)
        self.assertEqual(question_2.analysis_key, 'reason_unsatisfied')

        # We re-use the feedback app for pre-defined answers (that will allow
        # management of this questionnaire as if it was still implemented by
        # the feedback).
        happy_standard_answer = StandardAnswer.objects.filter(
            is_visible=True, is_satisfied=False, reopens_when_unhappy=True).first()

        answer_2 = QuestionnairesService.create_answer(
            happy_standard_answer.text, question_2, questionnaire, session=session)
        question_3 = QuestionnairesService.get_next_question(answer_2.payload, question_2, graph)
        self.assertEqual(question_3.analysis_key, 'extra_info')

        answer_3 = QuestionnairesService.create_answer(
            'Dit is extra informatie', question_3, questionnaire, session=session)
        question_4 = QuestionnairesService.get_next_question(answer_3.payload, question_3, graph)
        self.assertEqual(question_4.analysis_key, 'allows_contact')

        answer_4 = QuestionnairesService.create_answer(True, question_4, questionnaire, session=session)
        question_5 = QuestionnairesService.get_next_question(answer_4.payload, question_4, graph)
        self.assertIsNone(question_5, None)

# TODO: add tests for "unhappy" flow, make sure "bad" inputs cannot trip bad behavior
# TODO: revisit QuestionnairesService.validate_session_using_question_graph and
# QuestionnairesService.get_latest_answers_by_analysis_key

    def test_freeze_session_feedback_request_reopens(self):
        """
        Trigger a reopen request on Signal.
        """
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        # Create a session with all relevant questions answered
        session = FeedbackRequestService.create_session(signal)
        graph = session.questionnaire.graph
        a1 = AnswerFactory.create(session=session, question=graph.first_question, payload=False)

        outgoing_edge = Edge.objects.filter(
            graph=graph, question=graph.first_question, choice__payload=a1.payload).first()
        q_reason = outgoing_edge.next_question
        AnswerFactory.create(session=session, question=q_reason, payload='never good')  # trigger reopen request

        outgoing_edge = Edge.objects.filter(graph=graph, question=q_reason).first()
        q_extra_info = outgoing_edge.next_question
        AnswerFactory.create(session=session, question=q_extra_info, payload='EXTRA INFO')

        outgoing_edge = Edge.objects.filter(graph=graph, question=q_extra_info).first()
        q_allows_contact = outgoing_edge.next_question
        AnswerFactory.create(session=session, question=q_allows_contact, payload=True)

        session = QuestionnairesService.freeze_session(session)
        self.assertIsInstance(session, Session)
        self.assertEqual(Feedback.objects.count(), 1)
        signal.refresh_from_db()
        self.assertEqual(signal.status.state, workflow.VERZOEK_TOT_HEROPENEN)

        feedback = Feedback.objects.first()
        self.assertEqual(feedback.is_satisfied, False)
        self.assertEqual(feedback.text, 'never good')
        self.assertEqual(feedback.text_extra, 'EXTRA INFO')
        self.assertEqual(feedback.allows_contact, True)

    def test_freeze_session_feedback_request_does_not_reopen(self):
        """
        Give feedback without triggering reopen request on Signal.
        """
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        # Create a session with all relevant questions answered
        session = FeedbackRequestService.create_session(signal)
        graph = session.questionnaire.graph
        AnswerFactory.create(session=session, question=graph.first_question, payload=True)

        outgoing_edge = Edge.objects.filter(graph=graph, question=graph.first_question, choice__payload=True).first()
        q_reason = outgoing_edge.next_question
        AnswerFactory.create(session=session, question=q_reason, payload='all good')  # trigger reopen request

        outgoing_edge = Edge.objects.filter(graph=graph, question=q_reason).first()
        q_extra_info = outgoing_edge.next_question
        AnswerFactory.create(session=session, question=q_extra_info, payload='EXTRA INFO')

        outgoing_edge = Edge.objects.filter(graph=graph, question=q_extra_info).first()
        q_allows_contact = outgoing_edge.next_question
        AnswerFactory.create(session=session, question=q_allows_contact, payload=True)

        session = QuestionnairesService.freeze_session(session)
        self.assertIsInstance(session, Session)
        self.assertEqual(Feedback.objects.count(), 1)
        signal.refresh_from_db()
        self.assertEqual(signal.status.state, workflow.AFGEHANDELD)

        feedback = Feedback.objects.first()
        self.assertEqual(feedback.is_satisfied, True)
        self.assertEqual(feedback.text, 'all good')
        self.assertEqual(feedback.text_extra, 'EXTRA INFO')
        self.assertEqual(feedback.allows_contact, True)


class TestFeedbackToQuestionnaire(TestCase):
    def test_create_session_from_happy_feedback(self):
        feedback = FeedbackFactory.create(is_satisfied=True, text_extra='extra')
        session = FeedbackRequestService.create_session_from_feedback(feedback)

        self.assertIsInstance(session, Session)
        self.assertTrue(session.frozen)
        self.assertEqual(feedback.created_at + timedelta(days=FEEDBACK_REQUEST_DAYS_OPEN), session.submit_before)

        questions = Question.objects.get_from_question_graph(session.questionnaire.graph)
        questions_by_analysis_key = {q.analysis_key: q for q in questions}

        self.assertEqual(
            set(questions_by_analysis_key),
            {'satisfied', 'reason_satisfied', 'reason_unsatisfied', 'extra_info', 'allows_contact'}
        )
        answers = QuestionnairesService.get_latest_answers(session)
        answers_by_analysis_key = {a.question.analysis_key: a for a in answers}

        self.assertEqual(feedback.is_satisfied, answers_by_analysis_key['satisfied'].payload)
        self.assertEqual(feedback.text, answers_by_analysis_key['reason_satisfied'].payload)
        self.assertEqual(feedback.text_extra, answers_by_analysis_key['extra_info'].payload)
        self.assertEqual(feedback.allows_contact, answers_by_analysis_key['allows_contact'].payload)
