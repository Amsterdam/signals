# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta
from unittest import mock

from django.core.exceptions import ValidationError as django_validation_error
from django.test import TestCase

from signals.apps.questionnaires.app_settings import SESSION_DURATION
from signals.apps.questionnaires.exceptions import SessionInvalidated
from signals.apps.questionnaires.factories import (
    EdgeFactory,
    QuestionFactory,
    QuestionGraphFactory,
    QuestionnaireFactory,
    SessionFactory
)
from signals.apps.questionnaires.models import Answer, Choice, Questionnaire
from signals.apps.questionnaires.services import QuestionnairesService
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory


def _question_graph_with_decision():
    q1 = QuestionFactory.create(
        key='q_yesno',
        short_label='Yes or no?',
        label='Yes or no, what do you choose?',
    )
    q_yes = QuestionFactory.create(
        key='q_yes',
        short_label='yes',
        label='The yes question. Happy now?'
    )
    q_no = QuestionFactory.create(
        key='q_no',
        short_label='no',
        label='The no question. Still unhappy?'
    )

    graph = QuestionGraphFactory.create(name='Graph with decision', first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q_yes, payload='yes')
    EdgeFactory.create(graph=graph, question=q1, next_question=q_no, payload='no')

    return graph


def _question_graph_with_decision_null_keys():
    q1 = QuestionFactory.create(
        key=None,
        short_label='Yes or no?',
        label='Yes or no, what do you choose?',
    )
    q_yes = QuestionFactory.create(
        key=None,
        short_label='yes',
        label='The yes question. Happy now?'
    )
    q_no = QuestionFactory.create(
        key=None,
        short_label='no',
        label='The no question. Still unhappy?'
    )

    graph = QuestionGraphFactory.create(name='Graph with decision and null keys', first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q_yes, payload='yes')
    EdgeFactory.create(graph=graph, question=q1, next_question=q_no, payload='no')

    return graph


def _question_graph_with_decision_with_default():
    q1 = QuestionFactory.create(
        key='q_yesno',
        short_label='Yes or no?',
        label='Yes or no, what do you choose?',
    )
    q_yes = QuestionFactory.create(
        key='q_yes',
        short_label='yes',
        label='The yes question. Happy now?'
    )
    q_no = QuestionFactory.create(
        key='q_no',
        short_label='no',
        label='The no question. Still unhappy?'
    )

    graph = QuestionGraphFactory.create(name='Graph with decision with default', first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q_yes, payload='yes')
    EdgeFactory.create(graph=graph, question=q1, next_question=q_no, payload='no')
    EdgeFactory.create(graph=graph, question=q1, next_question=q_yes)  # Default option, last edge without payload prop.

    return graph


def _question_graph_no_required_answers():
    q1 = QuestionFactory.create(
        key='one',
        required=False,
        short_label='First not required',
        label='First not required',
    )
    q2 = QuestionFactory(
        key='two',
        required=False,
        short_label='Second not required',
        label='Second not required',
    )

    graph = QuestionGraphFactory.create(name='Graph with questions that are not required.', first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q2)

    return graph


def _question_graph_with_decision_with_default_no_required_answers():
    q1 = QuestionFactory.create(
        key='q_yesno',
        required=False,
        short_label='Yes or no?',
        label='Yes or no, what do you choose?',
    )
    q_yes = QuestionFactory.create(
        key='q_yes',
        short_label='yes',
        label='The yes question. Happy now?'
    )
    q_no = QuestionFactory.create(
        key='q_no',
        short_label='no',
        label='The no question. Still unhappy?'
    )

    graph = QuestionGraphFactory.create(
        name='Graph with questions that are not required and have defaults.', first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q_yes, payload='yes')
    EdgeFactory.create(graph=graph, question=q1, next_question=q_no, payload='no')
    EdgeFactory.create(graph=graph, question=q1, next_question=q_yes)

    return graph


def _question_graph_with_cycle():
    q1 = QuestionFactory.create(
        key='one',
        short_label='First question.',
        label='First question.',
    )
    q2 = QuestionFactory.create(
        key='two',
        short_label='Second question.',
        label='Second question.',
    )

    graph = QuestionGraphFactory.create(name='Graph with cycle', first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q2)
    EdgeFactory.create(graph=graph, question=q2, next_question=q1)

    return graph


def _question_graph_one_question():
    q1 = QuestionFactory.create(
        key='only',
        short_label='Only question.',
        label='Only question.',
    )

    return QuestionGraphFactory.create(name='Graph with only one question', first_question=q1)


class TestQuestionGraphs(TestCase):
    def test_all_question_graph(self):
        _question_graph_with_decision()
        _question_graph_with_decision_null_keys()
        _question_graph_with_cycle()


class TestQuestionnairesService(TestCase):
    def test_create_answers(self):
        # set up our questions and questionnaires
        graph = _question_graph_with_decision()
        questionnaire = QuestionnaireFactory.create(graph=graph)

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
        self.assertEqual(question2.ref, 'q_yes')

        answer2_str = 'yes'

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2, question2)
        self.assertIsNone(next_question)

    def test_create_answers_null_keys(self):
        graph = _question_graph_with_decision_null_keys()
        questionnaire = QuestionnaireFactory.create(graph=graph)

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
        # We want the yes branch followed, here we grab the relevant question
        edge_match = graph.edges.filter(question=question, payload=answer_str).first()
        self.assertEqual(question2, edge_match.next_question)

        answer2_str = 'yes'

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2, question2)
        self.assertIsNone(next_question)

    def test_get_next_question_ref(self):
        get_next_ref = QuestionnairesService.get_next_question_ref

        q_start = QuestionFactory.create(key='start', field_type='plain_text')

        # No next rules:
        empty_graph = QuestionGraphFactory.create(first_question=q_start)

        next_q = get_next_ref('ANSWER', q_start, empty_graph)
        self.assertIsNone(next_q)

        # Unconditional next:
        q2 = QuestionFactory.create()
        unconditional_graph = QuestionGraphFactory.create(first_question=q_start)
        EdgeFactory(graph=unconditional_graph, question=q_start, next_question=q2)

        next_ref = get_next_ref('ANSWER', q_start, unconditional_graph)
        self.assertEqual(next_ref, q2.ref)

        # conditional next, no default option:
        q_no = QuestionFactory.create(key='NO')
        q_yes = QuestionFactory.create(key='YES')
        conditional_graph = QuestionGraphFactory.create(first_question=q_start)
        EdgeFactory(graph=conditional_graph, question=q_start, next_question=q_no, payload='no')
        EdgeFactory(graph=conditional_graph, question=q_start, next_question=q_yes, payload='yes')

        self.assertIsNone(get_next_ref('ANSWER', q_start, conditional_graph))  # consider whether this is useful
        self.assertEqual(q_yes.ref, get_next_ref('yes', q_start, conditional_graph))
        self.assertEqual(q_no.ref, get_next_ref('no', q_start, conditional_graph))

        # conditional next with default:
        q_default = QuestionFactory.create(key='DEFAULT')
        conditional_with_default_graph = QuestionGraphFactory.create(first_question=q_start)
        EdgeFactory(graph=conditional_with_default_graph, question=q_start, next_question=q_no, payload='no')
        EdgeFactory(graph=conditional_with_default_graph, question=q_start, next_question=q_yes, payload='yes')
        EdgeFactory(graph=conditional_with_default_graph, question=q_start, next_question=q_default, payload=None)

        self.assertEqual(q_default.ref, get_next_ref('ANSWER', q_start, conditional_with_default_graph))
        self.assertEqual(q_yes.ref, get_next_ref('yes', q_start, conditional_with_default_graph))
        self.assertEqual(q_no.ref, get_next_ref('no', q_start, conditional_with_default_graph))

    def test_question_not_required(self):
        # set up our questions and questionnaires
        graph = _question_graph_no_required_answers()
        questionnaire = QuestionnaireFactory.create(graph=graph)

        question = questionnaire.graph.first_question
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
        self.assertEqual(question2.ref, 'two')

        answer2_str = None

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2, question2)
        self.assertIsNone(next_question)

    def test_question_with_default_next(self):
        # set up our questions and questionnaires
        graph = _question_graph_with_decision_with_default()
        questionnaire = QuestionnaireFactory.create(graph=graph)

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
        self.assertEqual(question2.ref, 'q_yes')  # get the default option

        answer2_str = 'Yippee'

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2, question2)
        self.assertIsNone(next_question)

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

    def test_validate_answer_payload_choices(self):
        graph = _question_graph_one_question()
        questionnaire = QuestionnaireFactory.create(graph=graph)

        payloads = ['only', 'yes', 'no']
        question = questionnaire.graph.first_question
        question.enforce_choices = True
        question.save()

        for payload in payloads:
            Choice.objects.create(question=question, payload=payload)

        self.assertEqual(question.choices.count(), 3)
        for payload in payloads:
            self.assertEqual(payload, QuestionnairesService.validate_answer_payload(payload, question))

        no_choice = 'NOT A VALID ANSWER GIVEN PREDEFINED CHOICES'
        with self.assertRaises(django_validation_error):
            QuestionnairesService.validate_answer_payload(no_choice, question)

        question.enforce_choices = False
        question.save()

        self.assertEqual(no_choice, QuestionnairesService.validate_answer_payload(no_choice, question))

    @mock.patch('signals.apps.questionnaires.services.questionnaires.QuestionnairesService.handle_frozen_session')
    def test_submit(self, patched_callback):
        graph = _question_graph_one_question()
        questionnaire = QuestionnaireFactory.create(graph=graph)

        question = questionnaire.graph.first_question
        answer_str = 'ONLY'

        # We will answer the questionnaire, until we reach a None next question.
        # In the first step we have no Session reference yet.
        with self.captureOnCommitCallbacks(execute=True):
            answer = QuestionnairesService.create_answer(
                answer_payload=answer_str, question=question, questionnaire=questionnaire, session=None)
        patched_callback.assert_not_called()

        self.assertIsInstance(answer, Answer)
        self.assertEqual(answer.question, question)

        session = answer.session
        self.assertIsNotNone(session)
        self.assertIsNone(session.submit_before)
        self.assertEqual(session.duration, timedelta(seconds=SESSION_DURATION))

        question2 = QuestionnairesService.get_next_question(answer, question)
        self.assertIsNone(question2)

        QuestionnairesService.freeze_session(session)
        patched_callback.assert_called_with(session)

    @mock.patch('signals.apps.questionnaires.services.questionnaires.QuestionnairesService.handle_frozen_session')
    def test_freeze_session(self, patched):
        graph = _question_graph_one_question()
        questionnaire = QuestionnaireFactory.create(graph=graph)

        question = questionnaire.first_question
        answer_str = 'ONLY'

        answer = QuestionnairesService.create_answer(
            answer_payload=answer_str, question=question, questionnaire=questionnaire, session=None)

        self.assertIsInstance(answer, Answer)
        self.assertEqual(answer.question, question)

        session = answer.session
        self.assertIsNotNone(session)
        self.assertIsNone(session.submit_before)
        self.assertEqual(session.duration, timedelta(seconds=SESSION_DURATION))

        session = QuestionnairesService.freeze_session(session)
        session.refresh_from_db()

        patched.assert_called_with(session)
        self.assertTrue(session.frozen)

    def test_get_session_reaction_request_flow(self):
        # A session for reaction request flow with no associated Signal should
        # raise an SessionInvalidated.
        session_no_signal = SessionFactory.create(questionnaire__flow=Questionnaire.REACTION_REQUEST)

        with self.assertRaises(SessionInvalidated):
            QuestionnairesService.get_session(session_no_signal.uuid)

        # A session for reaction request flow for a signal in a state other
        # than REACTIE_GEVRAAGD should raise SessionInvalidated.
        signal = SignalFactory.create()
        session = SessionFactory.create(_signal=signal, questionnaire__flow=Questionnaire.REACTION_REQUEST)

        with self.assertRaises(SessionInvalidated):
            QuestionnairesService.get_session(session.uuid)

        # A session for reaction request flow for a signal that also has a more
        # recent session, should raise SessionInvalidated.
        status = StatusFactory.create(state=workflow.REACTIE_GEVRAAGD)
        signal.status = status
        signal.save()
        SessionFactory.create(_signal=signal, questionnaire__flow=Questionnaire.REACTION_REQUEST)  # more recent

        with self.assertRaises(SessionInvalidated):
            QuestionnairesService.get_session(session.uuid)
