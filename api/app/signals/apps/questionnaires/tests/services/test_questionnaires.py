# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import datetime, timedelta
import unittest
from unittest import mock

from django.core.exceptions import ValidationError as django_validation_error
from django.test import TestCase
from freezegun import freeze_time

from signals.apps.questionnaires.app_settings import REACTION_REQUEST_DAYS_OPEN, SESSION_DURATION
from signals.apps.questionnaires.exceptions import SessionExpired, SessionFrozen, SessionInvalidated
from signals.apps.questionnaires.factories import (
    AnswerFactory,
    EdgeFactory,
    QuestionFactory,
    QuestionGraphFactory,
    QuestionnaireFactory,
    SessionFactory
)
from signals.apps.questionnaires.models import Answer, Choice, Question, Questionnaire, Session
from signals.apps.questionnaires.services import QuestionnairesService
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory


def _question_graph_with_decision():
    q1 = QuestionFactory.create(
        retrieval_key='q_yesno',
        short_label='Yes or no?',
        label='Yes or no, what do you choose?',
    )
    q_yes = QuestionFactory.create(
        retrieval_key='q_yes',
        short_label='yes',
        label='The yes question. Happy now?'
    )
    q_no = QuestionFactory.create(
        retrieval_key='q_no',
        short_label='no',
        label='The no question. Still unhappy?'
    )

    graph = QuestionGraphFactory.create(name='Graph with decision', first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q_yes, payload='yes')
    EdgeFactory.create(graph=graph, question=q1, next_question=q_no, payload='no')

    return graph


def _question_graph_with_decision_null_retrieval_keys():
    q1 = QuestionFactory.create(
        retrieval_key=None,
        short_label='Yes or no?',
        label='Yes or no, what do you choose?',
    )
    q_yes = QuestionFactory.create(
        retrieval_key=None,
        short_label='yes',
        label='The yes question. Happy now?'
    )
    q_no = QuestionFactory.create(
        retrieval_key=None,
        short_label='no',
        label='The no question. Still unhappy?'
    )

    graph = QuestionGraphFactory.create(name='Graph with decision and null keys', first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q_yes, payload='yes')
    EdgeFactory.create(graph=graph, question=q1, next_question=q_no, payload='no')

    return graph


def _question_graph_with_decision_with_default():
    q1 = QuestionFactory.create(
        retrieval_key='q_yesno',
        short_label='Yes or no?',
        label='Yes or no, what do you choose?',
    )
    q_yes = QuestionFactory.create(
        retrieval_key='q_yes',
        short_label='yes',
        label='The yes question. Happy now?'
    )
    q_no = QuestionFactory.create(
        retrieval_key='q_no',
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
        retrieval_key='one',
        required=False,
        short_label='First not required',
        label='First not required',
    )
    q2 = QuestionFactory(
        retrieval_key='two',
        required=False,
        short_label='Second not required',
        label='Second not required',
    )

    graph = QuestionGraphFactory.create(name='Graph with questions that are not required.', first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q2)

    return graph


def _question_graph_with_decision_with_default_no_required_answers():
    q1 = QuestionFactory.create(
        retrieval_key='q_yesno',
        required=False,
        short_label='Yes or no?',
        label='Yes or no, what do you choose?',
    )
    q_yes = QuestionFactory.create(
        retrieval_key='q_yes',
        short_label='yes',
        label='The yes question. Happy now?'
    )
    q_no = QuestionFactory.create(
        retrieval_key='q_no',
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
        retrieval_key='one',
        short_label='First question.',
        label='First question.',
    )
    q2 = QuestionFactory.create(
        retrieval_key='two',
        short_label='Second question.',
        label='Second question.',
    )

    graph = QuestionGraphFactory.create(name='Graph with cycle', first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q2)
    EdgeFactory.create(graph=graph, question=q2, next_question=q1)

    return graph


def _question_graph_one_question():
    q1 = QuestionFactory.create(
        retrieval_key='only',
        short_label='Only question.',
        label='Only question.',
    )

    return QuestionGraphFactory.create(name='Graph with only one question', first_question=q1)


def _create_graph_no_defaults(graph_name='diamond'):
    """
    Seed the database with a diamond shaped graph formed by questions.
    """
    q1 = QuestionFactory.create()
    q2 = QuestionFactory.create()
    q3 = QuestionFactory.create()

    # sketch:
    #    q1 <- first_question
    #   /  \
    # q2    q3

    graph = QuestionGraphFactory.create(name=graph_name, first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q2, payload='yes')
    EdgeFactory.create(graph=graph, question=q1, next_question=q3, payload='no')

    return graph


class TestQuestionGraphs(TestCase):
    def test_all_question_graph(self):
        _question_graph_with_decision()
        _question_graph_with_decision_null_retrieval_keys()
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

        question2 = QuestionnairesService.get_next_question(answer.payload, question, graph)
        self.assertEqual(question2.ref, 'q_yes')

        answer2_str = 'yes'

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2.payload, question2, graph)
        self.assertIsNone(next_question)

    def test_create_answers_retrieval_keys(self):
        graph = _question_graph_with_decision_null_retrieval_keys()
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

        question2 = QuestionnairesService.get_next_question(answer.payload, question, graph)
        # We want the yes branch followed, here we grab the relevant question
        edge_match = graph.edges.filter(question=question, payload=answer_str).first()
        self.assertEqual(question2, edge_match.next_question)

        answer2_str = 'yes'

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2.payload, question2, graph)
        self.assertIsNone(next_question)

    def test_get_next_question_ref(self):
        get_next = QuestionnairesService.get_next_question

        q_start = QuestionFactory.create(retrieval_key='start', field_type='plain_text')

        # No next rules:
        empty_graph = QuestionGraphFactory.create(first_question=q_start)

        next_q = get_next('ANSWER', q_start, empty_graph)
        self.assertIsNone(next_q)

        # Unconditional next:
        q2 = QuestionFactory.create()
        unconditional_graph = QuestionGraphFactory.create(first_question=q_start)
        EdgeFactory(graph=unconditional_graph, question=q_start, next_question=q2)

        next_ref = get_next('ANSWER', q_start, unconditional_graph)
        self.assertEqual(next_ref, q2)

        # conditional next, no default option:
        q_no = QuestionFactory.create(retrieval_key='NO')
        q_yes = QuestionFactory.create(retrieval_key='YES')
        conditional_graph = QuestionGraphFactory.create(first_question=q_start)
        EdgeFactory(graph=conditional_graph, question=q_start, next_question=q_no, payload='no')
        EdgeFactory(graph=conditional_graph, question=q_start, next_question=q_yes, payload='yes')

        self.assertIsNone(get_next('ANSWER', q_start, conditional_graph))  # consider whether this is useful
        self.assertEqual(q_yes, get_next('yes', q_start, conditional_graph))
        self.assertEqual(q_no, get_next('no', q_start, conditional_graph))

        # conditional next with default:
        q_default = QuestionFactory.create(retrieval_key='DEFAULT')
        conditional_with_default_graph = QuestionGraphFactory.create(first_question=q_start)
        EdgeFactory(graph=conditional_with_default_graph, question=q_start, next_question=q_no, payload='no')
        EdgeFactory(graph=conditional_with_default_graph, question=q_start, next_question=q_yes, payload='yes')
        EdgeFactory(graph=conditional_with_default_graph, question=q_start, next_question=q_default, payload=None)

        self.assertEqual(q_default, get_next('ANSWER', q_start, conditional_with_default_graph))
        self.assertEqual(q_yes, get_next('yes', q_start, conditional_with_default_graph))
        self.assertEqual(q_no, get_next('no', q_start, conditional_with_default_graph))

    @unittest.skip('get_next_question_ref will be removed')
    def test_get_next_question(self):
        get_next = QuestionnairesService.get_next_question

        q_start = QuestionFactory.create(retrieval_key='start', field_type='plain_text')

        # No next rules:
        empty_graph = QuestionGraphFactory.create(first_question=q_start)

        answer = AnswerFactory.create(payload='EMPTY', session__questionnaire__graph=empty_graph)
        next_q = get_next(answer, q_start)
        self.assertIsNone(next_q)

        # Unconditional next:
        q2 = QuestionFactory.create()
        unconditional_graph = QuestionGraphFactory.create(first_question=q_start)
        EdgeFactory(graph=unconditional_graph, question=q_start, next_question=q2)

        answer = AnswerFactory.create(payload='EMPTY', session__questionnaire__graph=unconditional_graph)
        next_q = get_next(answer, q_start)
        self.assertEqual(next_q, q2)

        # conditional next, no default option:
        q_no = QuestionFactory.create(retrieval_key='NO')
        q_yes = QuestionFactory.create(retrieval_key='YES')
        conditional_graph = QuestionGraphFactory.create(first_question=q_start)
        EdgeFactory(graph=conditional_graph, question=q_start, next_question=q_no, payload='no')
        EdgeFactory(graph=conditional_graph, question=q_start, next_question=q_yes, payload='yes')

        answer = AnswerFactory.create(payload='ANSWER', session__questionnaire__graph=conditional_graph)
        self.assertIsNone(get_next(answer, q_start))  # consider whether this is useful

        answer = AnswerFactory.create(payload='yes', session__questionnaire__graph=conditional_graph)
        self.assertEqual(q_yes, get_next(answer, q_start))

        answer = AnswerFactory.create(payload='no', session__questionnaire__graph=conditional_graph)
        self.assertEqual(q_no, get_next(answer, q_start))

        # conditional next with default:
        q_default = QuestionFactory.create(retrieval_key='DEFAULT')
        conditional_with_default_graph = QuestionGraphFactory.create(first_question=q_start)
        EdgeFactory(graph=conditional_with_default_graph, question=q_start, next_question=q_no, payload='no')
        EdgeFactory(graph=conditional_with_default_graph, question=q_start, next_question=q_yes, payload='yes')
        EdgeFactory(graph=conditional_with_default_graph, question=q_start, next_question=q_default, payload=None)

        answer = AnswerFactory.create(payload='ANSWER', session__questionnaire__graph=conditional_with_default_graph)
        self.assertEqual(q_default, get_next(answer, q_start))

        answer = AnswerFactory.create(payload='yes', session__questionnaire__graph=conditional_with_default_graph)
        self.assertEqual(q_yes, get_next(answer, q_start))

        answer = AnswerFactory.create(payload='no', session__questionnaire__graph=conditional_with_default_graph)
        self.assertEqual(q_no, get_next(answer, q_start))

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

        question2 = QuestionnairesService.get_next_question(answer.payload, question, graph)
        self.assertEqual(question2.ref, 'two')

        answer2_str = None

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2.payload, question2, graph)
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

        question2 = QuestionnairesService.get_next_question(answer.payload, question, graph)
        self.assertEqual(question2.ref, 'q_yes')  # get the default option

        answer2_str = 'Yippee'

        answer2 = QuestionnairesService.create_answer(
            answer_payload=answer2_str, question=question2, questionnaire=questionnaire, session=session)
        self.assertIsInstance(answer2, Answer)
        self.assertEqual(answer2.question, question2)
        self.assertEqual(answer2.session_id, session_id)

        next_question = QuestionnairesService.get_next_question(answer2.payload, question2, graph)
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

    def test_question_no_default_next(self):
        """
        Behavior of get_next_question when no default is set.
        """
        graph = _create_graph_no_defaults()
        questionnaire = QuestionnaireFactory(graph=graph)
        q1 = questionnaire.graph.first_question

        # Try following both branches:
        answer = QuestionnairesService.create_answer(answer_payload='yes', question=q1, questionnaire=questionnaire)
        self.assertIsNotNone(QuestionnairesService.get_next_question(answer.payload, q1, graph))

        answer = QuestionnairesService.create_answer(answer_payload='no', question=q1, questionnaire=questionnaire)
        self.assertIsNotNone(QuestionnairesService.get_next_question(answer.payload, q1, graph))

        # Try an answer that does not match a branch in the question graph.
        # Since the graph has no default question following the first question
        # we will get a next_question of None:
        answer = QuestionnairesService.create_answer(answer_payload='NADA', question=q1, questionnaire=questionnaire)
        self.assertIsNone(QuestionnairesService.get_next_question(answer.payload, q1, graph))

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

        question2 = QuestionnairesService.get_next_question(answer.payload, question, graph)
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
        signal = SignalFactory.create(status__state=workflow.GEMELD)
        session = SessionFactory.create(_signal=signal, questionnaire__flow=Questionnaire.REACTION_REQUEST)

        with self.assertRaises(SessionInvalidated) as cm:
            QuestionnairesService.get_session(session.uuid)
        self.assertIn('associated signal not in state REACTIE_GEVRAAGD', str(cm.exception))

        # A session for reaction request flow for a signal that also has a more
        # recent session, should raise SessionInvalidated.
        status = StatusFactory.create(state=workflow.REACTIE_GEVRAAGD)
        signal.status = status
        signal.save()
        SessionFactory.create(_signal=signal, questionnaire__flow=Questionnaire.REACTION_REQUEST)  # more recent

        with self.assertRaises(SessionInvalidated) as cm:
            QuestionnairesService.get_session(session.uuid)
        self.assertIn('a newer reaction request was issued', str(cm.exception))

    def test_get_session_expired(self):
        # A session that expired should raise a SessionExpired
        signal_created_at = datetime(2021, 8, 18, 12, 0, 0)
        submit_before = signal_created_at + timedelta(days=REACTION_REQUEST_DAYS_OPEN)
        get_session_at = signal_created_at + timedelta(days=REACTION_REQUEST_DAYS_OPEN * 2)

        with freeze_time(signal_created_at):
            signal = SignalFactory.create(status__state=workflow.GEMELD)
            session = SessionFactory.create(
                _signal=signal, questionnaire__flow=Questionnaire.EXTRA_PROPERTIES, submit_before=submit_before)

        with freeze_time(get_session_at):
            with self.assertRaises(SessionExpired) as cm:
                QuestionnairesService.get_session(session.uuid)
            self.assertIn('Expired!', str(cm.exception))

    def test_get_session_frozen(self):
        # A session that is frozen should raise SessionFrozen
        signal = SignalFactory.create(status__state=workflow.GEMELD)
        session = SessionFactory.create(_signal=signal, questionnaire__flow=Questionnaire.REACTION_REQUEST, frozen=True)
        with self.assertRaises(SessionFrozen) as cm:
            QuestionnairesService.get_session(session.uuid)
        self.assertIn('Already used!', str(cm.exception))


class TestGetAnswersFromSession(TestCase):
    def setUp(self):
        self.graph = _question_graph_with_decision()
        self.session = SessionFactory.create(questionnaire__graph=self.graph)

        with freeze_time('2021-08-17 12:00:00'):
            AnswerFactory.create(session=self.session, question=self.graph.first_question, payload='no')

        with freeze_time('2021-08-17 12:10:00'):
            AnswerFactory.create(session=self.session, question=self.graph.first_question, payload='yes')

        self.q2 = Question.objects.get(retrieval_key='q_yes')
        with freeze_time('2021-08-17 12:20:00'):
            AnswerFactory.create(session=self.session, question=self.q2, payload='yes happy')

    def test_get_latest_answers(self):
        answers = QuestionnairesService.get_latest_answers(self.session)
        self.assertEqual(answers.count(), 2)  # for duplicate answers we want only one

        answer_1 = answers.filter(question=self.graph.first_question)
        self.assertEqual(answer_1.count(), 1)
        self.assertEqual(answer_1.first().payload, 'yes')

        answer_2 = answers.filter(question=self.q2)
        self.assertEqual(answer_2.count(), 1)
        self.assertEqual(answer_2.first().payload, 'yes happy')

    def test_get_latest_answers_by_analysis_key(self):
        by_analysis_key = QuestionnairesService.get_latest_answers_by_analysis_key(self.session)
        self.assertEqual(len(by_analysis_key), 2)
        self.assertEqual(by_analysis_key[self.graph.first_question.analysis_key].payload, 'yes')
        self.assertEqual(by_analysis_key[self.q2.analysis_key].payload, 'yes happy')

    def test_get_latest_answers_by_uuid(self):
        by_uuid = QuestionnairesService.get_latest_answers_by_uuid(self.session)
        self.assertEqual(len(by_uuid), 2)
        self.assertEqual(by_uuid[self.graph.first_question.uuid].payload, 'yes')
        self.assertEqual(by_uuid[self.q2.uuid].payload, 'yes happy')

    def test_validate_session_using_question_graph(self):
        # TODO: move to different TestCase subclass
        session = QuestionnairesService.validate_session_using_question_graph(self.session)
        self.assertIsInstance(session, Session)
