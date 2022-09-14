# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import datetime, timedelta

import pytz
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
from signals.apps.questionnaires.models import Answer, Choice, Question, Questionnaire
from signals.apps.questionnaires.services import AnswerService
from signals.apps.questionnaires.services.utils import get_session_service
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
    EdgeFactory.create(graph=graph, question=q1, next_question=q_yes, choice__payload='yes', choice__question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q_no, choice__payload='no', choice__question=q1)

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
    EdgeFactory.create(graph=graph, question=q1, next_question=q_yes, choice__payload='yes', choice__question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q_no, choice__payload='no', choice__question=q1)

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
    EdgeFactory.create(graph=graph, question=q1, next_question=q_yes, choice__payload='yes', choice__question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q_no, choice__payload='no', choice__question=q1)
    # Default option, last edge without choice property:
    EdgeFactory.create(graph=graph, question=q1, next_question=q_yes, choice=None)

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
    EdgeFactory.create(graph=graph, question=q1, next_question=q2, choice=None)

    return graph


def _question_graph_with_decision_with_default_no_required_answers():
    # reuse the _question_graph_with_decision_with_default, but make question not-required
    graph = _question_graph_with_decision_with_default()
    graph.first_question.required = False
    graph.first_question.save()

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
    EdgeFactory.create(graph=graph, question=q1, next_question=q2, choice=None)
    EdgeFactory.create(graph=graph, question=q2, next_question=q1, choice=None)

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
    EdgeFactory.create(graph=graph, question=q1, next_question=q2, choice__payload='yes', choice__question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q3, choice__payload='no', choice__question=q1)

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
        questionnaire = QuestionnaireFactory.create(graph=graph, flow=Questionnaire.EXTRA_PROPERTIES)
        session = SessionFactory.create(questionnaire=questionnaire)
        session_service = get_session_service(session.uuid)
        session_service.refresh_from_db()

        question_1 = questionnaire.first_question
        answer_payload = 'yes'

        # We will answer the questionnaire, until we reach a None next question.
        # In the first step we have no Session reference yet.

        answer_1 = session_service.create_answer(answer_payload, question_1)
        self.assertIsInstance(answer_1, Answer)
        self.assertEqual(answer_1.question, question_1)

        session = answer_1.session
        session_id = session.id
        self.assertIsNotNone(session)
        self.assertIsNone(session.submit_before)
        self.assertEqual(session.duration, timedelta(seconds=SESSION_DURATION))

        question_2 = session_service.get_next_question(question_1, answer_1)
        self.assertEqual(question_2.ref, 'q_yes')

        answer_payload_2 = 'yes'
        answer_2 = session_service.create_answer(answer_payload_2, question_2)

        self.assertIsInstance(answer_2, Answer)
        self.assertEqual(answer_2.question, question_2)
        self.assertEqual(answer_2.session_id, session_id)

        next_question = session_service.get_next_question(question_2, answer_2)
        self.assertIsNone(next_question)

    def test_create_answers_retrieval_keys(self):
        graph = _question_graph_with_decision_null_retrieval_keys()
        questionnaire = QuestionnaireFactory.create(graph=graph)
        session = SessionFactory.create(questionnaire=questionnaire)
        session_service = get_session_service(session.uuid)
        session_service.refresh_from_db()

        question_1 = questionnaire.first_question
        answer_payload_1 = 'yes'

        # We will answer the questionnaire, until we reach a None next question.
        # In the first step we have no Session reference yet.
        answer_1 = session_service.create_answer(answer_payload_1, question_1)
        self.assertIsInstance(answer_1, Answer)
        self.assertEqual(answer_1.question, question_1)

        session = answer_1.session
        session_id = session.id
        self.assertIsNotNone(session)
        self.assertIsNone(session.submit_before)
        self.assertEqual(session.duration, timedelta(seconds=SESSION_DURATION))

        question_2 = session_service.get_next_question(question_1, answer_1)

        # We want the yes branch followed, here we grab the relevant question
        edge_match = graph.edges.filter(question=question_1, choice__payload=answer_payload_1).first()
        self.assertEqual(question_2, edge_match.next_question)

        answer_payload_2 = 'yes'

        answer_2 = session_service.create_answer(answer_payload_2, question_2)
        self.assertIsInstance(answer_2, Answer)
        self.assertEqual(answer_2.question, question_2)
        self.assertEqual(answer_2.session_id, session_id)

        next_question = session_service.get_next_question(question_2, answer_2)
        self.assertIsNone(next_question)

    def test_get_next_question_private(self):
        q_start = QuestionFactory.create(retrieval_key='start', field_type='plain_text')

        # No next rules:
        empty_graph = QuestionGraphFactory.create(first_question=q_start)

        session = SessionFactory.create(questionnaire__graph=empty_graph)
        session_service = get_session_service(session.uuid)
        session_service.refresh_from_db()

        next_q = session_service._get_next_question(
            session_service.question_graph_service._nx_graph,
            session_service.question_graph_service._questions_by_id,
            q_start,
            'ANSWER'
        )
        self.assertIsNone(next_q)

        # Unconditional next:
        q2 = QuestionFactory.create()
        unconditional_graph = QuestionGraphFactory.create(first_question=q_start)
        EdgeFactory(graph=unconditional_graph, question=q_start, next_question=q2, choice=None)

        session = SessionFactory.create(questionnaire__graph=unconditional_graph)
        session_service = get_session_service(session.uuid)
        session_service.refresh_from_db()

        next_q = session_service._get_next_question(
            session_service.question_graph_service._nx_graph,
            session_service.question_graph_service._questions_by_id,
            q_start,
            'ANSWER'
        )
        self.assertEqual(next_q, q2)

        # Conditional next, no default option:
        q_no = QuestionFactory.create(retrieval_key='NO')
        q_yes = QuestionFactory.create(retrieval_key='YES')
        conditional_graph = QuestionGraphFactory.create(first_question=q_start)
        EdgeFactory(graph=conditional_graph,
                    question=q_start,
                    next_question=q_no,
                    choice__payload='no',
                    choice__question=q_start)
        EdgeFactory(graph=conditional_graph,
                    question=q_start,
                    next_question=q_yes,
                    choice__payload='yes',
                    choice__question=q_start)

        session = SessionFactory.create(questionnaire__graph=conditional_graph)
        session_service = get_session_service(session.uuid)
        session_service.refresh_from_db()

        no_choice_question = session_service._get_next_question(
            session_service.question_graph_service._nx_graph,
            session_service.question_graph_service._questions_by_id,
            q_start,
            'ANSWER'
        )
        self.assertIsNone(no_choice_question)  # consider whether this is useful
        yes_question = session_service._get_next_question(
            session_service.question_graph_service._nx_graph,
            session_service.question_graph_service._questions_by_id,
            q_start,
            'yes'
        )
        self.assertEqual(q_yes, yes_question)
        no_question = session_service._get_next_question(
            session_service.question_graph_service._nx_graph,
            session_service.question_graph_service._questions_by_id,
            q_start,
            'no'
        )
        self.assertEqual(q_no, no_question)

        # Conditional next with default option defined:
        q_default = QuestionFactory.create(retrieval_key='DEFAULT')
        conditional_with_default_graph = QuestionGraphFactory.create(first_question=q_start)
        EdgeFactory(graph=conditional_with_default_graph,
                    question=q_start,
                    next_question=q_no,
                    choice__payload='no',
                    choice__question=q_start)
        EdgeFactory(graph=conditional_with_default_graph,
                    question=q_start,
                    next_question=q_yes,
                    choice__payload='yes',
                    choice__question=q_start)
        EdgeFactory(graph=conditional_with_default_graph,
                    question=q_start,
                    next_question=q_default,
                    choice=None)

        session = SessionFactory.create(questionnaire__graph=conditional_with_default_graph)
        session_service = get_session_service(session.uuid)
        session_service.refresh_from_db()

        no_choice_question = session_service._get_next_question(
            session_service.question_graph_service._nx_graph,
            session_service.question_graph_service._questions_by_id,
            q_start,
            'ANSWER'
        )
        self.assertEqual(no_choice_question, q_default)
        yes_question = session_service._get_next_question(
            session_service.question_graph_service._nx_graph,
            session_service.question_graph_service._questions_by_id,
            q_start,
            'yes'
        )
        self.assertEqual(yes_question, q_yes)
        no_question = session_service._get_next_question(
            session_service.question_graph_service._nx_graph,
            session_service.question_graph_service._questions_by_id,
            q_start,
            'no'
        )
        self.assertEqual(no_question, q_no)

    def test_question_not_required(self):
        # set up our questions and questionnaires
        graph = _question_graph_no_required_answers()
        questionnaire = QuestionnaireFactory.create(graph=graph)
        session = SessionFactory.create(questionnaire__graph=graph)
        session_service = get_session_service(session.uuid)
        session_service.refresh_from_db()

        question_1 = questionnaire.graph.first_question
        answer_payload_1 = None

        # We will answer the questionnaire, until we reach a None next question.
        # In the first step we have no Session reference yet.
        answer_1 = session_service.create_answer(answer_payload_1, question_1)
        self.assertIsInstance(answer_1, Answer)
        self.assertEqual(answer_1.question, question_1)

        session = answer_1.session
        session_id = session.id
        self.assertIsNotNone(session)
        self.assertIsNone(session.submit_before)
        self.assertEqual(session.duration, timedelta(seconds=SESSION_DURATION))

        question_2 = session_service.get_next_question(question_1, answer_1)
        self.assertEqual(question_2.ref, 'two')

        answer_payload_2 = None

        answer_2 = session_service.create_answer(answer_payload_2, question_2)
        self.assertIsInstance(answer_2, Answer)
        self.assertEqual(answer_2.question, question_2)
        self.assertEqual(answer_2.session_id, session_id)

        next_question = session_service.get_next_question(question_2, answer_2)
        self.assertIsNone(next_question)

    def test_question_with_default_next(self):
        # set up our questions and questionnaires
        graph = _question_graph_with_decision_with_default()
        session = SessionFactory.create(questionnaire__graph=graph)
        session_service = get_session_service(session.uuid)
        session_service.refresh_from_db()

        question_1 = session.questionnaire.first_question
        answer_payload_1 = 'WILL NOT MATCH ANYTHING'  # to trigger default

        # We will answer the questionnaire, until we reach a None next question.
        # In the first step we have no Session reference yet.
        answer_1 = session_service.create_answer(answer_payload_1, question_1)
        self.assertIsInstance(answer_1, Answer)
        self.assertEqual(answer_1.question, question_1)

        session = answer_1.session
        session_id = session.id
        self.assertIsNotNone(session)
        self.assertIsNone(session.submit_before)
        self.assertEqual(session.duration, timedelta(seconds=SESSION_DURATION))

        question_2 = session_service.get_next_question(question_1, answer_1)
        self.assertEqual(question_2.ref, 'q_yes')  # get the default option

        answer_payload_2 = 'Yippee'
        answer_2 = session_service.create_answer(answer_payload_2, question_2)
        self.assertIsInstance(answer_2, Answer)
        self.assertEqual(answer_2.question, question_2)
        self.assertEqual(answer_2.session_id, session_id)

        next_question = session_service.get_next_question(question_2, answer_2)
        self.assertIsNone(next_question)

    def test_question_no_default_next(self):
        """
        Behavior of get_next_question when no default is set.
        """
        graph = _create_graph_no_defaults()
        session = SessionFactory.create(questionnaire__graph=graph)
        session_service = get_session_service(session.uuid)
        session_service.refresh_from_db()

        question_1 = session.questionnaire.graph.first_question

        # Try following both branches:
        answer = session_service.create_answer('yes', question_1)
        self.assertIsNotNone(session_service.get_next_question(question_1, answer))

        answer = session_service.create_answer('no', question_1)
        self.assertIsNotNone(session_service.get_next_question(question_1, answer))

        # Try an answer that does not match a branch in the question graph.
        # Since the graph has no default question following the first question
        # we will get a next_question of None:
        answer = session_service.create_answer('NOT AN OPTION', question_1)
        self.assertIsNone(session_service.get_next_question(question_1, answer))

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
            self.assertEqual(payload, AnswerService.validate_answer_payload(payload, question))

        no_choice = 'NOT A VALID ANSWER GIVEN PREDEFINED CHOICES'
        with self.assertRaises(django_validation_error):
            AnswerService.validate_answer_payload(no_choice, question)

        question.enforce_choices = False
        question.save()

        self.assertEqual(no_choice, AnswerService.validate_answer_payload(no_choice, question))

    def test_freeze_session(self):
        graph = _question_graph_one_question()
        session = SessionFactory.create(questionnaire__graph=graph)
        session_service = get_session_service(session.uuid)
        session_service.refresh_from_db()

        question = session.questionnaire.first_question
        answer_payload = 'ONLY'

        answer = session_service.create_answer(answer_payload, question)
        self.assertIsInstance(answer, Answer)
        self.assertEqual(answer.question, question)

        session = answer.session
        self.assertIsNotNone(session)
        self.assertIsNone(session.submit_before)
        self.assertEqual(session.duration, timedelta(seconds=SESSION_DURATION))

        session_service.refresh_from_db()
        session_service.freeze()
        session = session_service.session
        session.refresh_from_db()

        self.assertTrue(session.frozen)

    def test_get_session_reaction_request_flow_no_signal(self):
        # A session for reaction request flow with no associated Signal should
        # raise an SessionInvalidated.
        session_no_signal = SessionFactory.create(questionnaire__flow=Questionnaire.REACTION_REQUEST)
        session_service_no_signal = get_session_service(session_no_signal.uuid)

        with self.assertRaises(SessionInvalidated):
            session_service_no_signal.is_publicly_accessible()

    def test_get_session_reaction_request_flow_two_requests(self):
        # A session for reaction request flow for a signal in a state other
        # than REACTIE_GEVRAAGD should raise SessionInvalidated.
        signal = SignalFactory.create(status__state=workflow.GEMELD)
        session = SessionFactory.create(_signal=signal, questionnaire__flow=Questionnaire.REACTION_REQUEST)
        session_service = get_session_service(session.uuid)

        with self.assertRaises(SessionInvalidated) as cm:
            session_service.is_publicly_accessible()
        self.assertIn('associated signal not in state REACTIE_GEVRAAGD', str(cm.exception))

        # A session for reaction request flow for a signal that also has a more
        # recent session, should raise SessionInvalidated.
        status = StatusFactory.create(state=workflow.REACTIE_GEVRAAGD)
        signal.status = status
        signal.save()
        SessionFactory.create(_signal=signal, questionnaire__flow=Questionnaire.REACTION_REQUEST)  # more recent
        session_service.refresh_from_db()

        with self.assertRaises(SessionInvalidated) as cm:
            session_service.is_publicly_accessible()
        self.assertIn('a newer reaction request was issued', str(cm.exception))

    def test_get_session_expired(self):
        # A session that expired should raise a SessionExpired
        signal_created_at = datetime(2021, 8, 18, 12, 0, 0, tzinfo=pytz.UTC)
        submit_before = signal_created_at + timedelta(days=REACTION_REQUEST_DAYS_OPEN)
        get_session_at = signal_created_at + timedelta(days=REACTION_REQUEST_DAYS_OPEN * 2)

        with freeze_time(signal_created_at):
            signal = SignalFactory.create(status__state=workflow.GEMELD)
            session = SessionFactory.create(
                _signal=signal, questionnaire__flow=Questionnaire.EXTRA_PROPERTIES, submit_before=submit_before)

        session_service = get_session_service(session.uuid)
        session_service.refresh_from_db()

        with freeze_time(get_session_at):
            with self.assertRaises(SessionExpired) as cm:
                session_service.is_publicly_accessible()
            self.assertIn('Expired!', str(cm.exception))

    def test_get_session_frozen(self):
        # A session that is frozen should raise SessionFrozen
        signal = SignalFactory.create(status__state=workflow.GEMELD)
        session = SessionFactory.create(_signal=signal, questionnaire__flow=Questionnaire.REACTION_REQUEST, frozen=True)
        session_service = get_session_service(session.uuid)
        session_service.refresh_from_db()

        with self.assertRaises(SessionFrozen) as cm:
            session_service.is_publicly_accessible()
        self.assertIn('Already used!', str(cm.exception))


class TestGetAnswersFromSession(TestCase):
    def setUp(self):
        self.graph = _question_graph_with_decision()
        self.session = SessionFactory.create(questionnaire__graph=self.graph)

        with freeze_time('2021-08-17 12:00:00+00:00'):
            AnswerFactory.create(session=self.session, question=self.graph.first_question, payload='no')

        with freeze_time('2021-08-17 12:10:00+00:00'):
            AnswerFactory.create(session=self.session, question=self.graph.first_question, payload='yes')

        self.q2 = Question.objects.get(retrieval_key='q_yes')
        with freeze_time('2021-08-17 12:20:00+00:00'):
            AnswerFactory.create(session=self.session, question=self.q2, payload='yes happy')

    def test_get_latest_answers(self):
        session_service = get_session_service(self.session.uuid)
        answers = session_service._get_all_answers(self.session)

        self.assertEqual(len(answers), 2)  # for duplicate answers we want only one

    def test_answers_by_analysis_key(self):
        session_service = get_session_service(self.session.uuid)
        session_service.refresh_from_db()
        by_analysis_key = session_service.answers_by_analysis_key
        self.assertEqual(len(by_analysis_key), 2)
        self.assertEqual(by_analysis_key[self.graph.first_question.analysis_key].payload, 'yes')
        self.assertEqual(by_analysis_key[self.q2.analysis_key].payload, 'yes happy')

    def test_get_latest_answers_by_uuid(self):
        session_service = get_session_service(self.session.uuid)
        session_service.refresh_from_db()
        by_uuid = session_service.answers_by_question_uuid
        self.assertEqual(len(by_uuid), 2)
        self.assertEqual(by_uuid[self.graph.first_question.uuid].payload, 'yes')
        self.assertEqual(by_uuid[self.q2.uuid].payload, 'yes happy')


class TestValidateSessionUsingQuestionGraph(TestCase):

    def test_validate_question_graph_with_decision(self):
        graph = _question_graph_with_decision()
        q_yes = Question.objects.get(retrieval_key='q_yes')
        q_no = Question.objects.get(retrieval_key='q_no')

        # Test yes branch
        session_1 = SessionFactory.create(questionnaire__graph=graph)
        AnswerFactory(session=session_1, question=graph.first_question, payload='yes')
        AnswerFactory(session=session_1, question=q_yes, payload='yes happy')

        session_service_1 = get_session_service(session_1.uuid)
        session_service_1.refresh_from_db()
        self.assertTrue(session_service_1.can_freeze)

        # Test no branch
        session_2 = SessionFactory.create(questionnaire__graph=graph)
        AnswerFactory(session=session_2, question=graph.first_question, payload='no')
        AnswerFactory(session=session_2, question=q_no, payload='no unhappy')

        session_service_2 = get_session_service(session_2.uuid)
        session_service_2.refresh_from_db()
        self.assertTrue(session_service_2.can_freeze)

        # Test missing data
        session_3 = SessionFactory.create(questionnaire__graph=graph)
        AnswerFactory(session=session_3, question=graph.first_question, payload='yes')

        session_service_3 = get_session_service(session_3.uuid)
        session_service_3.refresh_from_db()
        self.assertFalse(session_service_3.can_freeze)

        # Test showing a question halfway through the questionnaire can be
        # considered an endpoint.
        # TODO: consider whether this behavior is desirable (likely not).
        session_4 = SessionFactory.create(questionnaire__graph=graph)
        AnswerFactory(session=session_4, question=graph.first_question, payload='not a choice, but valid')

        session_service_4 = get_session_service(session_4.uuid)
        session_service_4.refresh_from_db()
        self.assertFalse(session_service_4.can_freeze)

    def test_validate_question_graph_with_decision_with_default_required(self):
        graph = _question_graph_with_decision_with_default()
        q_yes = Question.objects.get(retrieval_key='q_yes')

        # Test default branch by not providing an answer, that will fail because
        # the first question is required.
        session_1 = SessionFactory.create(questionnaire__graph=graph)
        AnswerFactory(session=session_1, question=q_yes, payload='yes happy')

        session_service_1 = get_session_service(session_1.uuid)
        session_service_1.refresh_from_db()
        self.assertFalse(session_service_1.can_freeze)

        # Test default branch (by providing a non-matching, but valid answer)
        session_2 = SessionFactory.create(questionnaire__graph=graph)
        AnswerFactory(session=session_2, question=graph.first_question, payload='not a choice, but valid')
        AnswerFactory(session=session_2, question=q_yes, payload='yes happy')

        session_service_2 = get_session_service(session_2.uuid)
        session_service_2.refresh_from_db()
        self.assertTrue(session_service_2.can_freeze)

    def test_validate_question_graph_with_decision_with_default_not_required(self):
        graph = _question_graph_with_decision_with_default_no_required_answers()
        q_yes = Question.objects.get(retrieval_key='q_yes')
        q_no = Question.objects.get(retrieval_key='q_no')

        # Test default branch by not providing an answer, that will work because
        # the first question is not required.
        session_1 = SessionFactory.create(questionnaire__graph=graph)
        AnswerFactory(session=session_1, question=q_yes, payload='yes happy')

        session_service_1 = get_session_service(session_1.uuid)
        session_service_1.refresh_from_db()

        self.assertTrue(session_service_1.can_freeze)

        # Test default branch (by providing a non-matching, but valid answer).
        # This case will fail because the default branch is chosen.
        session_2 = SessionFactory.create(questionnaire__graph=graph)
        AnswerFactory(session=session_2, question=q_no, payload='not happy')

        session_service_2 = get_session_service(session_2.uuid)
        session_service_2.refresh_from_db()

        self.assertFalse(session_service_2.can_freeze)
