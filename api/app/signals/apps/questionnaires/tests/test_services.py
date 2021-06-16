# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta

from django.core.exceptions import ValidationError as django_validation_error
from django.test import TestCase

from signals.apps.questionnaires.factories import QuestionFactory, QuestionnaireFactory
from signals.apps.questionnaires.models import SESSION_DURATION, Answer
from signals.apps.questionnaires.services import QuestionnairesService


def _question_graph_with_decision():
    q1 = QuestionFactory.create(
        key='q_yesno',
        short_label='Yes or no?',
        label='Yes or no, what do you choose?',
        next_rules=[
            {'ref': 'q_yes', 'payload': 'yes'},
            {'ref': 'q_no', 'payload': 'no'},
        ],
    )
    q2 = QuestionFactory.create(
        key='q_yes',
        short_label='yes',
        label='The yes question. Happy now?'
    )
    q3 = QuestionFactory.create(
        key='q_no',
        short_label='no',
        label='The no question. Still unhappy?'
    )

    return q1, q2, q3


def _question_graph_with_decision_null_keys():
    q2 = QuestionFactory.create(
        key=None,
        short_label='yes',
        label='The yes question. Happy now?'
    )
    q3 = QuestionFactory.create(
        key=None,
        short_label='no',
        label='The no question. Still unhappy?'
    )
    q1 = QuestionFactory.create(
        key=None,
        short_label='Yes or no?',
        label='Yes or no, what do you choose?',
        next_rules=[
            {'ref': str(q2.uuid), 'payload': 'yes'},
            {'ref': str(q3.uuid), 'payload': 'no'},
        ],
    )

    return q1, q2, q3


def _question_graph_with_decision_with_default():
    q1 = QuestionFactory.create(
        key='q_yesno',
        short_label='Yes or no?',
        label='Yes or no, what do you choose?',
        next_rules=[
            {'ref': 'q_yes', 'payload': 'yes'},
            {'ref': 'q_no', 'payload': 'no'},
            {'ref': 'q_yes'}  # Default option, always last and without 'payload' property!
        ],
    )
    q2 = QuestionFactory.create(
        key='q_yes',
        short_label='yes',
        label='The yes question. Happy now?'
    )
    q3 = QuestionFactory.create(
        key='q_no',
        short_label='no',
        label='The no question. Still unhappy?'
    )

    return q1, q2, q3


def _question_graph_no_required_answers():
    q1 = QuestionFactory.create(
        key='one',
        required=False,
        short_label='First not required',
        label='First not required',
        next_rules=[
            {'ref': 'two'},
        ]
    )
    q2 = QuestionFactory(
        key='two',
        required=False,
        short_label='Second not required',
        label='Second not required',
    )

    return q1, q2


def _question_graph_with_decision_with_default_no_required_answers():
    q1 = QuestionFactory.create(
        key='q_yesno',
        required=False,
        short_label='Yes or no?',
        label='Yes or no, what do you choose?',
        next_rules=[
            {'ref': 'q_yes', 'payload': 'yes'},
            {'ref': 'q_no', 'payload': 'no'},
            {'ref': 'q_yes'}  # Default option, always last and without 'payload' property!
        ],
    )
    q2 = QuestionFactory.create(
        key='q_yes',
        short_label='yes',
        label='The yes question. Happy now?'
    )
    q3 = QuestionFactory.create(
        key='q_no',
        short_label='no',
        label='The no question. Still unhappy?'
    )

    return q1, q2, q3


def _question_graph_with_cycle():
    q1 = QuestionFactory.create(
        key='one',
        short_label='First question.',
        label='First question.',
        next_rules=[
            {'ref': 'two'}
        ],
    )
    q2 = QuestionFactory.create(
        key='two',
        short_label='Second question.',
        label='Second question.',
        next_rules=[
            {'ref': 'one'}
        ],
    )

    return q1, q2


def _question_graph_one_question():
    q1 = QuestionFactory.create(
        key='only',
        short_label='Only question.',
        label='Only question.',
    )
    return q1


class TestQuestionGraphs(TestCase):
    def test_all_question_graph(self):
        _question_graph_with_decision()
        _question_graph_with_decision_null_keys()
        _question_graph_with_cycle()


class TestQuestionnairesService(TestCase):
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
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2, question2)
        self.assertEqual(next_question.key, 'submit')

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
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2, question2)
        self.assertEqual(next_question.key, 'submit')

    def test_get_next_question_ref(self):
        q_next_rules_no_next = []
        q_next_rules_next_none = None
        q_next_rules_next_unconditional = [{'ref': 'UNCONDITIONAL'}]
        q_next_rules_next_conditional = [{'ref': 'NO', 'payload': 'no'}, {'ref': 'YES', 'payload': 'yes'}]
        q_next_rules_next_conditional_with_default = [
            {'ref': 'NO', 'payload': 'no'}, {'ref': 'YES', 'payload': 'yes'}, {'ref': 'DEFAULT'}
        ]

        get_next = QuestionnairesService.get_next_question_ref
        self.assertEqual(get_next('yes', q_next_rules_no_next), None)
        self.assertEqual(get_next('yes', q_next_rules_next_none), None)  # <-- problematic
        self.assertEqual(get_next('WILL NOT MATCH', q_next_rules_next_conditional), None)
        self.assertEqual(get_next('BLAH', q_next_rules_next_unconditional), 'UNCONDITIONAL')
        self.assertEqual(get_next('yes', q_next_rules_next_conditional), 'YES')
        self.assertEqual(get_next('no', q_next_rules_next_conditional), 'NO')
        self.assertEqual(get_next('WILL NOT MATCH', q_next_rules_next_conditional_with_default), 'DEFAULT')

    def test_question_not_required(self):
        # set up our questions and questionnaires
        q1, q2 = _question_graph_no_required_answers()
        questionnaire = QuestionnaireFactory.create(first_question=q1)

        question = questionnaire.first_question
        answer_str = None

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
        self.assertEqual(question2.ref, q2.ref)

        answer2_str = None

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2, question2)
        self.assertEqual(next_question.key, 'submit')

    def test_question_with_default_next(self):
        # set up our questions and questionnaires
        q_yesno, q_yes, q_no = _question_graph_with_decision_with_default()
        questionnaire = QuestionnaireFactory.create(first_question=q_yesno)

        question = questionnaire.first_question
        answer_str = 'WILL NOT MATCH ANYTHING'  # to trigger default

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
        self.assertEqual(question2.ref, q_yes.ref)  # get the default option

        answer2_str = 'Yippee'

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2, question2)
        self.assertEqual(next_question.key, 'submit')

    def test_validate_answer_payload(self):
        integer_question = QuestionFactory(field_type='integer', label='integer', short_label='integer')
        plaintext_question = QuestionFactory(
            field_type='plain_text', label='plain_text', short_label='plain_text')
        validate_answer = QuestionnairesService.validate_answer_payload

        # Check integer fieldtype
        self.assertEqual(validate_answer(123456, integer_question), 123456)
        with self.assertRaises(django_validation_error):
            QuestionnairesService.validate_answer_payload('THESE ARE CHARACTERS', integer_question)
        with self.assertRaises(django_validation_error):
            QuestionnairesService.validate_answer_payload({'some': 'thing', 'complicated': {}}, integer_question)

        # check plain_text fieldtype
        self.assertEqual(validate_answer('THIS IS TEXT', plaintext_question), 'THIS IS TEXT')
        with self.assertRaises(django_validation_error):
            QuestionnairesService.validate_answer_payload(123456, plaintext_question)
        with self.assertRaises(django_validation_error):
            QuestionnairesService.validate_answer_payload({'some': 'thing', 'complicated': {}}, plaintext_question)

    def test_submit(self):
        q1 = _question_graph_one_question()
        questionnaire = QuestionnaireFactory.create(first_question=q1)

        question = questionnaire.first_question
        answer_str = 'ONLY'

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
        self.assertEqual(question2.ref, 'submit')

        answer2_str = None

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2, question2)
        self.assertIsNone(next_question)
