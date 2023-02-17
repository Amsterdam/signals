# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import datetime, timedelta

import pytz
from django.core.exceptions import ValidationError as django_validation_error
from django.test import TestCase
from freezegun import freeze_time

from signals.apps.questionnaires.exceptions import CycleDetected, SessionExpired, SessionFrozen
from signals.apps.questionnaires.factories import (
    AnswerFactory,
    ChoiceFactory,
    QuestionFactory,
    SessionFactory
)
from signals.apps.questionnaires.models import Answer, Edge
from signals.apps.questionnaires.services.session import SessionService
from signals.apps.questionnaires.tests.test_models import (
    create_cycle,
    create_diamond_plus,
    create_empty
)


class TestSessionService(TestCase):
    def test_get_all_answers(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)
        service.question_graph_service.refresh_from_db()
        self.assertEqual(len(service.question_graph_service._questions_by_id), 7)

        for q in service.question_graph_service._questions:
            AnswerFactory.create(session=session, question=q, payload='answer')
        answers = service._get_all_answers(session)
        self.assertEqual(len(answers), 7)

    def test_get_next_question_no_choices_predefined(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)
        service.question_graph_service.refresh_from_db()
        self.assertEqual(len(service.question_graph_service._questions_by_id), 7)

        # First question in "diamond_plus" QuestionGraph is a decision point,
        # the create_diamond_plus function does not set choices or edge order
        # explicitly. We test the decision point here by answering the first
        # question, determining the next question and reordering the edges
        # and checking we get the other branch.
        a = Answer.objects.create(session=session, question=q_graph.first_question, payload='answer')
        next_question_1 = service._get_next_question(
            service.question_graph_service._nx_graph,
            service.question_graph_service._questions_by_id,
            q_graph.first_question,
            a.payload
        )

        # First set order to the old order, nothing should change.
        edge_ids_before = q_graph.get_edge_order(q_graph.first_question)
        edge_ids_after = q_graph.set_edge_order(q_graph.first_question, edge_ids_before)
        service.question_graph_service.refresh_from_db()  # reload, because cache is now stale

        self.assertEqual(list(edge_ids_before), list(edge_ids_after))
        next_question_2 = service._get_next_question(
            service.question_graph_service._nx_graph,
            service.question_graph_service._questions_by_id,
            q_graph.first_question,
            a.payload
        )
        self.assertEqual(next_question_1.id, next_question_2.id)  # nothing should change

        # Now change the order of outgoing edges from q_graph.first_question
        edge_ids_before = q_graph.get_edge_order(q_graph.first_question)
        new_order = list(reversed(edge_ids_before))
        edge_ids_after = q_graph.set_edge_order(q_graph.first_question, new_order)
        self.assertNotEqual(list(edge_ids_after), list(edge_ids_before))
        service.question_graph_service.refresh_from_db()  # reload, because cache is now stale

        self.assertEqual(list(edge_ids_after), list(new_order))
        next_question_3 = service._get_next_question(
            service.question_graph_service._nx_graph,
            service.question_graph_service._questions_by_id,
            q_graph.first_question,
            a.payload
        )
        self.assertNotEqual(next_question_1.id, next_question_3.id)  # should have changed

    def test_get_next_question_with_choices_predefined(self):
        # Update QuestionGraph with predefined choices
        c2 = ChoiceFactory.create(payload='q2')
        c3 = ChoiceFactory.create(payload='q3')

        q_graph = create_diamond_plus()
        edge_to_q2 = Edge.objects.filter(
            question=q_graph.first_question, graph=q_graph, next_question__analysis_key='q2')
        edge_to_q3 = Edge.objects.filter(
            question=q_graph.first_question, graph=q_graph, next_question__analysis_key='q3')

        self.assertEqual(edge_to_q2.count(), 1)
        self.assertEqual(edge_to_q3.count(), 1)

        edge_to_q2.update(choice=c2)
        edge_to_q3.update(choice=c3)

        # ---
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)
        service.question_graph_service.refresh_from_db()
        self.assertEqual(len(service.question_graph_service._questions_by_id), 7)

        a1 = Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload='NOT A PREDEFINED CHOICE',  # This is something we should not allow!
        )
        next_question_1 = service._get_next_question(
            service.question_graph_service._nx_graph,
            service.question_graph_service._questions_by_id,
            q_graph.first_question,
            a1.payload
        )
        self.assertIsNone(next_question_1)

        a2 = Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload='q2'
        )
        next_question_2 = service._get_next_question(
            service.question_graph_service._nx_graph,
            service.question_graph_service._questions_by_id,
            q_graph.first_question,
            a2.payload
        )
        self.assertEqual(next_question_2.analysis_key, 'q2')

        a3 = Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload='q3'
        )
        next_question_3 = service._get_next_question(
            service.question_graph_service._nx_graph,
            service.question_graph_service._questions_by_id,
            q_graph.first_question,
            a3.payload
        )
        self.assertEqual(next_question_3.analysis_key, 'q3')

    def test_get_reachable_questions_answers_graph_with_cycles(self):
        q_graph = create_cycle()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)
        service.question_graph_service.refresh_from_db()

        answers = service._get_all_answers(session)
        answers_by_question_id = {a.question.id: a for a in answers}

        with self.assertRaises(CycleDetected):
            service._get_reachable_questions_and_answers(
                service.question_graph_service._nx_graph,
                service.question_graph_service._q_graph.first_question,
                service.question_graph_service._questions_by_id,
                answers_by_question_id
            )

    def test_get_reachable_questions_answers_no_answers(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)
        service.question_graph_service.refresh_from_db()

        answers = service._get_all_answers(session)
        answers_by_question_id = {a.question.id: a for a in answers}

        questions_by_id, unanswered_by_id, answers_by_id, can_freeze = service._get_reachable_questions_and_answers(
            service.question_graph_service._nx_graph,
            service.question_graph_service._q_graph.first_question,
            service.question_graph_service._questions_by_id,
            answers_by_question_id
        )
        self.assertEqual(len(questions_by_id), 4)  # should only return questions on one branch
        self.assertEqual(len(unanswered_by_id), 4)  # should only return questions on one branch
        self.assertEqual(len(answers_by_id), 0)  # no answers yet
        self.assertFalse(can_freeze)

    def test_get_reachable_questions_answers_one_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)
        service.question_graph_service.refresh_from_db()

        # Answer questions
        Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload='q1'
        )

        answers = service._get_all_answers(session)
        answers_by_question_id = {a.question.id: a for a in answers}

        questions_by_id, unanswered_by_id, answers_by_id, can_freeze = service._get_reachable_questions_and_answers(
            service.question_graph_service._nx_graph,
            service.question_graph_service._q_graph.first_question,
            service.question_graph_service._questions_by_id,
            answers_by_question_id
        )
        self.assertEqual(len(questions_by_id), 4)  # should only return questions on one branch
        self.assertEqual(len(unanswered_by_id), 3)
        self.assertEqual(len(answers_by_id), 1)  # one question answered
        self.assertFalse(can_freeze)

    def test_get_reachable_questions_answers_one_path(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.refresh_from_db()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service._questions}

        # Answer questions
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q1'],
            payload='q1'
        )
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q2'],
            payload='q2'
        )
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q4'],
            payload='q4'
        )
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q5'],
            payload='q5'
        )

        answers = service._get_all_answers(session)
        answers_by_question_id = {a.question.id: a for a in answers}

        questions_by_id, unanswered_by_id, answers_by_id, can_freeze = service._get_reachable_questions_and_answers(
            service.question_graph_service._nx_graph,
            service.question_graph_service._q_graph.first_question,
            service.question_graph_service._questions_by_id,
            answers_by_question_id
        )

        self.assertEqual(len(questions_by_id), 4)  # should only return questions on one branch
        self.assertEqual(len(unanswered_by_id), 0)
        self.assertEqual(len(answers_by_id), 4)  # all questions answered
        self.assertTrue(can_freeze)

    def test_answers_by_analysis_key_no_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        answers_by_analysis_key = service.answers_by_analysis_key  # this does a refresh_from_db

        self.assertEqual(answers_by_analysis_key, dict())
        self.assertEqual(len(answers_by_analysis_key), 0)

    def test_answers_by_analysis_key_one_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # Answer questions
        Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload='q1'
        )
        service.refresh_from_db()
        answers_by_analysis_key = service.answers_by_analysis_key

        self.assertEqual(len(answers_by_analysis_key), 1)
        self.assertIn('q1', answers_by_analysis_key)
        self.assertEqual(answers_by_analysis_key['q1'].payload, 'q1')

    def test_answers_by_analysis_key_one_path(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.refresh_from_db()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service._questions}

        # Answer questions
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q1'],
            payload='q1'
        )
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q2'],
            payload='q2'
        )
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q4'],
            payload='q4'
        )
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q5'],
            payload='q5'
        )

        service.refresh_from_db()
        answers_by_analysis_key = service.answers_by_analysis_key

        self.assertEqual(len(answers_by_analysis_key), 4)
        for key in ['q1', 'q2', 'q4', 'q5']:
            self.assertEqual(answers_by_analysis_key[key].payload, key)

    def test_get_extra_properties_no_answers(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        extra_properties = service.get_extra_properties('URL')  # this does a refresh_from_db
        self.assertEqual(extra_properties, [])

        extra_properties_no_url = service.get_extra_properties()
        self.assertEqual(extra_properties_no_url, [])

    def test_get_extra_properties_one_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # Answer questions
        Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload='q1'
        )
        service.refresh_from_db()
        extra_properties = service.get_extra_properties('URL')

        self.assertEqual(len(extra_properties), 1)
        self.assertEqual(extra_properties[0]['category_url'], 'URL')
        self.assertEqual(extra_properties[0]['label'], q_graph.first_question.short_label)

        extra_properties_no_url = service.get_extra_properties()

        self.assertEqual(len(extra_properties_no_url), 1)
        self.assertNotIn('category_url', extra_properties_no_url[0])

    def test_get_extra_properties_one_path(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.refresh_from_db()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service._questions}

        # Answer questions
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q1'],
            payload='q1'
        )
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q2'],
            payload='q2'
        )
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q4'],
            payload='q4'
        )
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q5'],
            payload='q5'
        )

        service.refresh_from_db()
        extra_properties = service.get_extra_properties('URL')
        self.assertEqual(len(extra_properties), 4)
        self.assertEqual(extra_properties[0]['category_url'], 'URL')

        extra_properties_no_url = service.get_extra_properties()
        self.assertEqual(len(extra_properties_no_url), 4)
        self.assertNotIn('category_url', extra_properties_no_url[0])

    def test_can_freeze_no_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        self.assertFalse(service.can_freeze)  # this does a refresh_from_db

    def test_can_freeze_one_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # Answer questions
        Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload='q1'
        )
        service.refresh_from_db()
        self.assertFalse(service.can_freeze)

    def test_can_freeze_one_path(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.refresh_from_db()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service._questions}

        # Answer questions
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q1'],
            payload='q1'
        )
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q2'],
            payload='q2'
        )
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q4'],
            payload='q4'
        )
        Answer.objects.create(
            session=session,
            question=q_by_analysis_key['q5'],
            payload='q5'
        )

        service.refresh_from_db()
        self.assertTrue(service.can_freeze)

    def test_create_answer_one_path(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.refresh_from_db()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service._questions}

        # Answer questions
        service.create_answer('q1', q_by_analysis_key['q1'])
        service.create_answer('q2', q_by_analysis_key['q2'])
        service.create_answer('q4', q_by_analysis_key['q4'])
        service.create_answer('q5', q_by_analysis_key['q5'])

        service.refresh_from_db()
        answers_by_analysis_key = service.answers_by_analysis_key

        self.assertEqual(len(answers_by_analysis_key), 4)
        for key in ['q1', 'q2', 'q4', 'q5']:
            self.assertEqual(answers_by_analysis_key[key].payload, key)

        # Test our is_accessible here:
        service.is_publicly_accessible()

    def test_create_answer_session_expired(self):
        # expired session must not accept answers
        t_creation = datetime(2021, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)
        t_now = datetime(2021, 6, 1, 0, 0, 0, tzinfo=pytz.UTC)

        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph, created_at=t_creation, submit_before=t_creation)
        service = SessionService(session)
        service.refresh_from_db()

        first_question = service.path_questions[0]
        with freeze_time(t_now):
            with self.assertRaises(SessionExpired):
                service.create_answer('TOO LATE', first_question)

    def test_create_answer_session_frozen(self):
        # frozen session must not accept answers
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph, frozen=True)
        service = SessionService(session)
        service.refresh_from_db()

        first_question = service.path_questions[0]
        with self.assertRaises(SessionFrozen):
            service.create_answer('SESSION IS FROZEN', first_question)

    def test_create_answer_not_associated_to_questionnaire(self):
        # you cannot answer questions not part of the questionnaire associated with current session
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        bad_question = QuestionFactory.create()

        with self.assertRaises(django_validation_error) as cm:
            service.create_answer('WILL NOT BE ACCEPTED', bad_question)
        self.assertIn('not in questionnaire', cm.exception.message)

    def test_is_publicly_accessible_frozen_session(self):
        # Sessions that are frozen are no longer publicly accessible:
        q_graph = create_diamond_plus()
        session_frozen = SessionFactory.create(questionnaire__graph=q_graph, frozen=True)
        service_frozen = SessionService(session_frozen)
        with self.assertRaises(SessionFrozen):
            service_frozen.is_publicly_accessible()

    def test_is_publicly_accessible_expired_session(self):
        q_graph = create_diamond_plus()
        # Sessions that have expired because the submit_before deadline was
        # passed are no longer publicly available:
        t_creation = datetime(2021, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)
        t_now = datetime(2021, 6, 1, 0, 0, 0, tzinfo=pytz.UTC)

        session_expired_i = SessionFactory.create(
            questionnaire__graph=q_graph,
            created_at=t_creation,
            started_at=None,
            submit_before=t_creation + timedelta(days=7),
            duration=None,
            frozen=False
        )
        service_expired_i = SessionService(session_expired_i)

        with freeze_time(t_now):
            with self.assertRaises(SessionExpired):
                service_expired_i.is_publicly_accessible()

        # Sessions that have expired because too long was taken to fill out
        # the questionnaire are no longer publicly available:
        session_expired_ii = SessionFactory.create(
            questionnaire__graph=q_graph,
            created_at=t_creation,
            started_at=t_creation,
            submit_before=None,
            duration=timedelta(seconds=60 * 60 * 2),
            frozen=False
        )
        service_expired_ii = SessionService(session_expired_ii)
        with freeze_time(t_now):
            with self.assertRaises(SessionExpired):
                service_expired_ii.is_publicly_accessible()

    def test_answers_by_question_uuid_no_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        answers_by_question_uuid = service.answers_by_question_uuid
        self.assertEqual(answers_by_question_uuid, {})

    def test_answers_by_question_uuid_one_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # Answer questions
        Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload='q1'
        )

        service.refresh_from_db()
        answers_by_question_uuid = service.answers_by_question_uuid
        self.assertIsInstance(answers_by_question_uuid, dict)
        self.assertEqual(len(answers_by_question_uuid), 1)

    def test_answers_by_question_uuid_one_path(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.refresh_from_db()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service._questions}

        # Answer questions
        service.create_answer(str(q_by_analysis_key['q1'].uuid), q_by_analysis_key['q1'])
        service.create_answer(str(q_by_analysis_key['q2'].uuid), q_by_analysis_key['q2'])
        service.create_answer(str(q_by_analysis_key['q4'].uuid), q_by_analysis_key['q4'])
        service.create_answer(str(q_by_analysis_key['q5'].uuid), q_by_analysis_key['q5'])

        service.refresh_from_db()
        answers_by_question_uuid = service.answers_by_question_uuid

        self.assertEqual(len(answers_by_question_uuid), 4)
        for key in ['q1', 'q2', 'q4', 'q5']:
            uuid = q_by_analysis_key[key].uuid
            self.assertEqual(answers_by_question_uuid[uuid].payload, str(uuid))

    def test_create_answers_one_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.refresh_from_db()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service._questions}

        # Answer questions
        service.create_answers(['q1'], [q_by_analysis_key['q1']])

        self.assertEqual(len(service.answers_by_analysis_key), 1)
        self.assertEqual(service.answers_by_analysis_key['q1'].payload, 'q1')
        self.assertEqual(len(service.path_validation_errors_by_uuid), 0)
        self.assertEqual(len(service.path_answered_question_uuids), 1)
        self.assertEqual(len(service.path_unanswered_question_uuids), 3)

    def test_create_answers_one_path(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.refresh_from_db()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service._questions}

        # Answer questions
        service.create_answers(
            ['q1', 'q2', 'q4', 'q5'],
            [
                q_by_analysis_key['q1'],
                q_by_analysis_key['q2'],
                q_by_analysis_key['q4'],
                q_by_analysis_key['q5']
            ]
        )

        service.refresh_from_db()
        answers_by_analysis_key = service.answers_by_analysis_key

        self.assertEqual(len(answers_by_analysis_key), 4)
        for key in ['q1', 'q2', 'q4', 'q5']:
            self.assertEqual(answers_by_analysis_key[key].payload, key)

        self.assertTrue(service.can_freeze)
        self.assertEqual(len(service.path_validation_errors_by_uuid), 0)
        self.assertEqual(len(service.path_answered_question_uuids), 4)
        self.assertEqual(len(service.path_unanswered_question_uuids), 0)

    def test_create_answers_one_path_all_bad(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.refresh_from_db()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service._questions}

        # Answer questions
        service.create_answers(
            [1, 2, 4, 5],  # will not survive fieldtype check
            [
                q_by_analysis_key['q1'],
                q_by_analysis_key['q2'],
                q_by_analysis_key['q4'],
                q_by_analysis_key['q5']
            ]
        )

        service.refresh_from_db()
        answers_by_analysis_key = service.answers_by_analysis_key

        self.assertEqual(len(answers_by_analysis_key), 0)
        path_validation_errors_by_uuid = service.path_validation_errors_by_uuid

        self.assertEqual(len(path_validation_errors_by_uuid), 4)
        self.assertEqual(
            set(path_validation_errors_by_uuid), {q_by_analysis_key[key].uuid for key in ['q1', 'q2', 'q4', 'q5']})

        self.assertFalse(service.can_freeze)
        self.assertEqual(len(service.path_validation_errors_by_uuid), 4)
        self.assertEqual(len(service.path_answered_question_uuids), 0)
        self.assertEqual(len(service.path_unanswered_question_uuids), 4)

    def test_get_extra_properties_one_answer_selected_object(self):
        q_graph = create_empty()
        q1 = QuestionFactory.create(analysis_key='q1', field_type='selected_object')
        q_graph.first_question = q1
        q_graph.save()

        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # Answer questions
        answer = Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload={
                'id': 'C-123.456_test',
                'type': 'container',
                'onMap': True,
                'coordinates': {
                    'lat': 4.90022563,
                    'lng': 52.36768424
                }
            }
        )
        service.refresh_from_db()
        extra_properties = service.get_extra_properties('URL')

        self.assertEqual(len(extra_properties), 1)
        self.assertEqual(extra_properties[0]['category_url'], 'URL')
        self.assertEqual(extra_properties[0]['id'], answer.question.analysis_key)
        self.assertEqual(extra_properties[0]['label'], answer.question.short_label)
        self.assertEqual(extra_properties[0]['answer']['id'], answer.payload['id'])
        self.assertEqual(extra_properties[0]['answer']['type'], answer.payload['type'])
        self.assertEqual(extra_properties[0]['answer']['location']['coordinates']['lat'],
                         answer.payload['coordinates']['lat'])
        self.assertEqual(extra_properties[0]['answer']['location']['coordinates']['lng'],
                         answer.payload['coordinates']['lng'])
