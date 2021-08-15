# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils.timezone import make_aware
from freezegun import freeze_time

from signals.apps.feedback.factories import StandardAnswerFactory
from signals.apps.feedback.models import StandardAnswer
from signals.apps.questionnaires.app_settings import FEEDBACK_REQUEST_DAYS_OPEN
from signals.apps.questionnaires.exceptions import WrongState
from signals.apps.questionnaires.factories import SessionFactory
from signals.apps.questionnaires.models import Question, Session
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

        self.assertEqual(questionnaire.first_question.key, 'satisfied')
        all_questions = Question.objects.get_from_question_graph(graph)
        self.assertEqual(all_questions.count(), 5)
        reachable_questions = Question.objects.get_reachable_from_question_graph(graph)
        self.assertEqual(reachable_questions.count(), 5)

    @unittest.expectedFailure
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
        question_1 = questionnaire.graph.first_question
        self.assertEqual(question_1.ref, 'satisfied')

        answer_1 = QuestionnairesService.create_answer('ja', question_1, questionnaire, session=session)
        question_2 = QuestionnairesService.get_next_question(answer_1, question_1)
        self.assertEqual(question_2.ref, 'reason_satisfied')

        # We re-use the feedback app for pre-defined answers (that will allow
        # management of this questionnaire as if it was still implemented by
        # the feedback).
        happy_standard_answer = StandardAnswer.objects.filter(
            is_visible=True, is_satisfied=True, reopens_when_unhappy=False).first()

        answer_2 = QuestionnairesService.create_answer(
            happy_standard_answer.text, question_2, questionnaire, session=session)
        question_3 = QuestionnairesService.get_next_question(answer_2, question_2)
        self.assertEqual(question_3.ref, 'extra_info')

        answer_3 = QuestionnairesService.create_answer(
            'Dit is extra informatie', question_3, questionnaire, session=session)
        question_4 = QuestionnairesService.get_next_question(answer_3, question_3)
        self.assertEqual(question_4.ref, 'allow_contact')

        answer_4 = QuestionnairesService.create_answer(
            'ja', question_4, questionnaire, session=session)
        question_5 = QuestionnairesService.get_next_question(answer_4, question_4)
        self.assertIsNone(question_5, None)

    def test_fill_out_questionnaire_unsatisfied(self):
        # Check predefined questionnaire structure, then fill out the questionnaire.
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        session = FeedbackRequestService.create_session(signal)
        questionnaire = session.questionnaire
        question_1 = questionnaire.graph.first_question
        self.assertEqual(question_1.ref, 'satisfied')

        answer_1 = QuestionnairesService.create_answer('nee', question_1, questionnaire, session=session)
        question_2 = QuestionnairesService.get_next_question(answer_1, question_1)
        self.assertEqual(question_2.ref, 'reason_unsatisfied')

        # We re-use the feedback app for pre-defined answers (that will allow
        # management of this questionnaire as if it was still implemented by
        # the feedback).
        happy_standard_answer = StandardAnswer.objects.filter(
            is_visible=True, is_satisfied=False, reopens_when_unhappy=True).first()

        answer_2 = QuestionnairesService.create_answer(
            happy_standard_answer.text, question_2, questionnaire, session=session)
        question_3 = QuestionnairesService.get_next_question(answer_2, question_2)
        self.assertEqual(question_3.ref, 'extra_info')

        answer_3 = QuestionnairesService.create_answer(
            'Dit is extra informatie', question_3, questionnaire, session=session)
        question_4 = QuestionnairesService.get_next_question(answer_3, question_3)
        self.assertEqual(question_4.ref, 'allow_contact')

        answer_4 = QuestionnairesService.create_answer(
            'ja', question_4, questionnaire, session=session)
        question_5 = QuestionnairesService.get_next_question(answer_4, question_4)
        self.assertIsNone(question_5, None)
