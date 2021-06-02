# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta

from django.test import TestCase

from signals.apps.questionnaires.factories import QuestionFactory, QuestionnaireFactory
from signals.apps.questionnaires.models import SESSION_DURATION, Answer
from signals.apps.questionnaires.services import QuestionnairesService


def _question_graph_with_decision():
    q1 = QuestionFactory.create(key='q_yesno', payload={
        'shortLabel': 'Yes or no?',
        'label': 'Yes or no, what do you choose?',
        'next': [
            {'ref': 'q_yes', 'payload': 'yes'},
            {'ref': 'q_no', 'payload': 'no'},
        ],
    })

    q2 = QuestionFactory.create(key='q_yes', payload={
        'shortLabel': 'yes',
        'label': 'The yes question. Happy now?'
    })

    q3 = QuestionFactory.create(key='q_no', payload={
        'shortLabel': 'no',
        'label': 'The no question. Still unhappy?'
    })

    return q1, q2, q3


def _question_graph_with_decision_null_keys():
    q2 = QuestionFactory.create(key=None, payload={
        'shortLabel': 'yes',
        'label': 'The yes question. Happy now?'
    })

    q3 = QuestionFactory.create(key=None, payload={
        'shortLabel': 'no',
        'label': 'The no question. Still unhappy?'
    })

    q1 = QuestionFactory.create(key=None, payload={
        'shortLabel': 'Yes or no?',
        'label': 'Yes or no, what do you choose?',
        'next': [
            {'ref': str(q2.uuid), 'payload': 'yes'},
            {'ref': str(q3.uuid), 'payload': 'no'},
        ],
    })

    return q1, q2, q3


def _question_graph_with_cycle():
    q1 = QuestionFactory.create(key='one', payload={
        'shortLabel': 'First question.',
        'label': 'First question.',
        'next': [
            {'ref': 'two'}
        ],
    })

    q2 = QuestionFactory.create(key='two', payload={
        'shortLabel': 'First question.',
        'label': 'First question.',
        'next': [
            {'ref': 'one'}
        ],
    })

    return q1, q2


class TestQuestionGraphs(TestCase):
    def test_all_question_graph(self):
        _question_graph_with_decision()
        _question_graph_with_decision_null_keys()
        _question_graph_with_cycle()


class TestQuestionnaireService(TestCase):
    def test_create_answers(self):
        # set up our questions and questionnaires
        q_yesno, q_yes, q_no = _question_graph_with_decision()
        questionnaire = QuestionnaireFactory.create(first_question=q_yesno)

        question = questionnaire.first_question
        answer_str = 'yes'

        # We will answer the questionnaire, until we reach a None next question.
        # In the first step we have no Session reference yet.
        answer = QuestionnairesService.create_answer(
            answer_payload=answer_str, question=question, questionnaire=questionnaire, session=None)
        self.assertIsInstance(answer, Answer)
        self.assertEqual(answer.question, question)

        session = answer.session
        session_id = session.id
        self.assertIsNotNone(session)
        self.assertIsNone(session.submit_before)
        self.assertEqual(session.duration, timedelta(seconds=SESSION_DURATION))

        question2 = QuestionnairesService.get_next_question(answer, question)
        self.assertEqual(question2.ref, q_yes.key)

        answer2_str = 'yes'

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str,
            question=question2,
            questionnaire=questionnaire,
            session=session
        )
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_key2 = QuestionnairesService.get_next_question(answer2, question2)
        self.assertIsNone(next_key2)

    def test_create_answers_null_keys(self):
        q_yesno, q_yes, q_no = _question_graph_with_decision_null_keys()
        questionnaire = QuestionnaireFactory.create(first_question=q_yesno)

        question = questionnaire.first_question
        answer_str = 'yes'

        # We will answer the questionnaire, until we reach a None next question.
        # In the first step we have no Session reference yet.
        answer = QuestionnairesService.create_answer(
            answer_payload=answer_str, question=question, questionnaire=questionnaire, session=None)
        self.assertIsInstance(answer, Answer)
        self.assertEqual(answer.question, question)

        session = answer.session
        session_id = session.id
        self.assertIsNotNone(session)
        self.assertIsNone(session.submit_before)
        self.assertEqual(session.duration, timedelta(seconds=SESSION_DURATION))

        question2 = QuestionnairesService.get_next_question(answer, question)
        self.assertEqual(question2.ref, q_yes.uuid)

        answer2_str = 'yes'

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str,
            question=question2,
            questionnaire=questionnaire,
            session=session
        )
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_key2 = QuestionnairesService.get_next_question(answer2, question2)
        self.assertIsNone(next_key2)
