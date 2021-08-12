# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils.timezone import make_aware
from freezegun import freeze_time

from signals.apps.questionnaires.app_settings import FEEDBACK_REQUEST_DAYS_OPEN
from signals.apps.questionnaires.exceptions import WrongState
from signals.apps.questionnaires.factories import SessionFactory
from signals.apps.questionnaires.models import Question
from signals.apps.questionnaires.services import FeedbackRequestService, QuestionnairesService
from signals.apps.signals.factories import SignalFactory
from signals.apps.signals import workflow


from signals.apps.feedback.factories import StandardAnswerFactory


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

    def test_fill_out_questionnaire(self):
        signal = SignalFactory.create(status__state=workflow.AFGEHANDELD)
        session = FeedbackRequestService.create_session(signal)
        questionnaire = session.questionnaire
        graph = questionnaire.graph

        answer = QuestionnairesService.create_answer('ja', graph.first_question, questionnaire, session=session)
        next_question = QuestionnairesService.get_next_question(answer, graph.first_question)
        self.assertEqual(next_question.)

        # Test happy flow, reopen flow in test method t
        happy_answer = StandardAnswerFactory.objects.filter(
            is_visible=True, is_satisfied=True, reopens_when_unhappy=False).first()

    def test_fill_out_questionnaire_reopen_signal(self):
        pass
