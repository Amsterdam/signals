# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.core.exceptions import ValidationError as django_validation_error
from django.test import TestCase
from networkx import MultiDiGraph

from signals.apps.questionnaires.factories import (
    AnswerFactory,
    ChoiceFactory,
    QuestionFactory,
    SessionFactory
)
from signals.apps.questionnaires.models import Answer, Edge, Questionnaire, Session
from signals.apps.questionnaires.services.busy import (
    AnswerService,
    QuestionGraphService,
    SessionService
)
from signals.apps.questionnaires.tests.test_models import create_diamond_plus


class TestAnswerService(TestCase):
    def test_validated_answer_payload_not_required(self):
        q = QuestionFactory.create(required=False)
        self.assertEqual(AnswerService.validate_answer_payload(None, q), None)
        self.assertEqual(AnswerService.validate_answer_payload('BLAH', q), 'BLAH')
        with self.assertRaises(django_validation_error):
            AnswerService.validate_answer_payload(['NOT', 'A', 'STRING'], q)

    def test_validated_answer_payload_required(self):
        q = QuestionFactory.create(required=True)
        self.assertEqual(AnswerService.validate_answer_payload('BLAH', q), 'BLAH')
        with self.assertRaises(django_validation_error):
            AnswerService.validate_answer_payload(None, q)
        with self.assertRaises(django_validation_error):
            AnswerService.validate_answer_payload(['NOT', 'A', 'STRING'], q)

    def test_validate_answer_payload_do_not_enforce_choices(self):
        q = QuestionFactory.create(required=False, enforce_choices=False)
        ChoiceFactory.create(question=q, payload='VALID')
        self.assertEqual(AnswerService.validate_answer_payload('VALID', q), 'VALID')
        self.assertEqual(AnswerService.validate_answer_payload('BLAH', q), 'BLAH')

    def test_validate_answer_payload_do_enforce_choices(self):
        q = QuestionFactory.create(required=False, enforce_choices=True)
        ChoiceFactory.create(question=q, payload='VALID')
        self.assertEqual(AnswerService.validate_answer_payload('VALID', q), 'VALID')
        with self.assertRaises(django_validation_error):
            AnswerService.validate_answer_payload('BLAH', q)


class TestQuestionGraphService(TestCase):
    def test_get_edges(self):
        q_graph = create_diamond_plus()
        service = QuestionGraphService(q_graph)

        edges = service._get_edges(q_graph)
        self.assertEqual(len(edges), 6)

    def test_build_nx_graph_no_choices_predefined(self):
        q_graph = create_diamond_plus()
        service = QuestionGraphService(q_graph)
        edges = service._get_edges(q_graph)

        nx_graph = service._build_nx_graph(q_graph, edges)
        self.assertIsInstance(nx_graph, MultiDiGraph)
        self.assertEqual(len(nx_graph.nodes), 7)

    def test_get_all_questions(self):
        q_graph = create_diamond_plus()
        service = QuestionGraphService(q_graph)
        edges = service._get_edges(q_graph)
        nx_graph = service._build_nx_graph(q_graph, edges)

        questions = service._get_all_questions(nx_graph)
        self.assertEqual(len(questions), 7)
        self.assertEqual({q.analysis_key for q in questions}, set(f'q{n}' for n in range(1, 8)))

    def test_get_reachable_questions(self):
        q_graph = create_diamond_plus()
        service = QuestionGraphService(q_graph)
        edges = service._get_edges(q_graph)
        nx_graph = service._build_nx_graph(q_graph, edges)

        service.q_graph = q_graph
        service.nx_graph = nx_graph
        questions = service.get_reachable_questions()
        self.assertEqual(len(questions), 5)
        self.assertEqual({q.analysis_key for q in questions}, set(f'q{n}' for n in range(1, 6)))

    def test_load_question_data(self):
        q_graph = create_diamond_plus()
        service = QuestionGraphService(q_graph)

        service.load_question_data()
        self.assertEqual(len(service.edges), 6)
        self.assertIsInstance(service.nx_graph, MultiDiGraph)
        self.assertEqual(len(service.nx_graph.nodes), 7)
        self.assertEqual(len(service.questions), 7)
        self.assertEqual(len(service.questions_by_id), 7)


class TestSessionService(TestCase):
    def test_get_all_answers(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)
        service.question_graph_service.load_question_data()
        self.assertEqual(len(service.question_graph_service.questions_by_id), 7)

        for q in service.question_graph_service.questions:
            AnswerFactory.create(session=session, question=q, payload='answer')
        answers = service._get_all_answers(session)
        self.assertEqual(len(answers), 7)

    def test_get_next_question_no_choices_predefined(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)
        service.question_graph_service.load_question_data()
        self.assertEqual(len(service.question_graph_service.questions_by_id), 7)

        # First question in "diamond_plus" QuestionGraph is a decision point,
        # the create_diamond_plus function does not set choices or edge order
        # explicitly. We test the decision point here by answering the first
        # question, determining the next question and reordering the edges
        # and checking we get the other branch.
        a = Answer.objects.create(session=session, question=q_graph.first_question, payload='answer')
        next_question_1 = service._get_next_question(
            service.question_graph_service.nx_graph,
            service.question_graph_service.questions_by_id,
            q_graph.first_question,
            a.payload
        )

        # First set order to the old order, nothing should change.
        edge_ids_before = q_graph.get_edge_order(q_graph.first_question)
        edge_ids_after = q_graph.set_edge_order(q_graph.first_question, edge_ids_before)
        service.question_graph_service.load_question_data()  # reload, because cache is now stale

        self.assertEqual(list(edge_ids_before), list(edge_ids_after))
        next_question_2 = service._get_next_question(
            service.question_graph_service.nx_graph,
            service.question_graph_service.questions_by_id,
            q_graph.first_question,
            a.payload
        )
        self.assertEqual(next_question_1.id, next_question_2.id)  # nothing should change

        # Now change the order of outgoing edges from q_graph.first_question
        edge_ids_before = q_graph.get_edge_order(q_graph.first_question)
        new_order = list(reversed(edge_ids_before))
        edge_ids_after = q_graph.set_edge_order(q_graph.first_question, new_order)
        self.assertNotEqual(list(edge_ids_after), list(edge_ids_before))
        service.question_graph_service.load_question_data()  # reload, because cache is now stale

        self.assertEqual(list(edge_ids_after), list(new_order))
        next_question_3 = service._get_next_question(
            service.question_graph_service.nx_graph,
            service.question_graph_service.questions_by_id,
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
        service.question_graph_service.load_question_data()
        self.assertEqual(len(service.question_graph_service.questions_by_id), 7)

        a1 = Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload='NOT A PREDEFINED CHOICE',  # This is something we should not allow!
        )
        next_question_1 = service._get_next_question(
            service.question_graph_service.nx_graph,
            service.question_graph_service.questions_by_id,
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
            service.question_graph_service.nx_graph,
            service.question_graph_service.questions_by_id,
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
            service.question_graph_service.nx_graph,
            service.question_graph_service.questions_by_id,
            q_graph.first_question,
            a3.payload
        )
        self.assertEqual(next_question_3.analysis_key, 'q3')

    def test_get_reachable_questions_answers_no_answers(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)
        service.question_graph_service.load_question_data()

        answers = service._get_all_answers(session)
        answers_by_question_id = {a.question.id: a for a in answers}

        questions_by_id, unanswered_by_id, answers_by_id, can_freeze = service._get_reachable_questions_and_answers(
            service.question_graph_service.nx_graph,
            service.question_graph_service.q_graph.first_question,
            service.question_graph_service.questions_by_id,
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
        service.question_graph_service.load_question_data()

        # Answer questions
        Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload='q1'
        )

        answers = service._get_all_answers(session)
        answers_by_question_id = {a.question.id: a for a in answers}

        questions_by_id, unanswered_by_id, answers_by_id, can_freeze = service._get_reachable_questions_and_answers(
            service.question_graph_service.nx_graph,
            service.question_graph_service.q_graph.first_question,
            service.question_graph_service.questions_by_id,
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
        service.question_graph_service.load_question_data()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service.questions}

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
            service.question_graph_service.nx_graph,
            service.question_graph_service.q_graph.first_question,
            service.question_graph_service.questions_by_id,
            answers_by_question_id
        )

        self.assertEqual(len(questions_by_id), 4)  # should only return questions on one branch
        self.assertEqual(len(unanswered_by_id), 0)
        self.assertEqual(len(answers_by_id), 4)  # all questions answered
        self.assertTrue(can_freeze)

    def test_get_answers_by_analysis_key_no_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        service.load_data()
        answers_by_analysis_key = service.get_answers_by_analysis_key()

        self.assertEqual(answers_by_analysis_key, dict())

    def test_get_answers_by_analysis_key_one_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # Answer questions
        Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload='q1'
        )
        service.load_data()
        answers_by_analysis_key = service.get_answers_by_analysis_key()

        self.assertEqual(len(answers_by_analysis_key), 1)
        self.assertIn('q1', answers_by_analysis_key)
        self.assertEqual(answers_by_analysis_key['q1'].payload, 'q1')

    def test_get_answers_by_analysis_key_one_path(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.load_question_data()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service.questions}

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

        service.load_data()
        answers_by_analysis_key = service.get_answers_by_analysis_key()

        self.assertEqual(len(answers_by_analysis_key), 4)
        for key in ['q1', 'q2', 'q4', 'q5']:
            self.assertEqual(answers_by_analysis_key[key].payload, key)

    def test_get_extra_properties_no_answers(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        service.load_data()
        extra_properties = service.get_extra_properties('URL')

        self.assertEqual(extra_properties, [])

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
        service.load_data()
        extra_properties = service.get_extra_properties('URL')

        self.assertEqual(len(extra_properties), 1)
        self.assertEqual(extra_properties[0]['category_url'], 'URL')
        self.assertEqual(extra_properties[0]['label'], q_graph.first_question.short_label)

    def test_get_extra_properties_one_path(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.load_question_data()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service.questions}

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

        service.load_data()
        extra_properties = service.get_extra_properties('URL')

        self.assertEqual(len(extra_properties), 4)

    def test_get_can_freeze_no_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        service.load_data()
        self.assertFalse(service.get_can_freeze())

    def test_get_can_freeze_one_answer(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # Answer questions
        Answer.objects.create(
            session=session,
            question=q_graph.first_question,
            payload='q1'
        )
        service.load_data()
        self.assertFalse(service.get_can_freeze())

    def test_get_can_freeze_one_path(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.load_question_data()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service.questions}

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

        service.load_data()
        self.assertTrue(service.get_can_freeze())

    def test_from_questionnaire(self):
        q_graph = create_diamond_plus()
        questionnaire = Questionnaire.objects.create(
            name='Test questionnaire',
            description='Just a test',
            is_active=True,
            graph=q_graph,
            flow=Questionnaire.EXTRA_PROPERTIES
        )

        service = SessionService.from_questionnaire(questionnaire)
        self.assertIsInstance(service, SessionService)
        self.assertIsInstance(service.session, Session)
        service.load_data()

        self.assertIsInstance(service.question_graph_service, QuestionGraphService)
        self.assertEqual(len(service.question_graph_service.nx_graph.nodes), 7)
        self.assertEqual(len(service.answers), 0)

    def test_create_answer_one_path(self):
        q_graph = create_diamond_plus()
        session = SessionFactory.create(questionnaire__graph=q_graph)
        service = SessionService(session)

        # get references to questions
        service.question_graph_service.load_question_data()
        q_by_analysis_key = {q.analysis_key: q for q in service.question_graph_service.questions}

        # Answer questions
        service.create_answer('q1', q_by_analysis_key['q1'])
        service.create_answer('q2', q_by_analysis_key['q2'])
        service.create_answer('q4', q_by_analysis_key['q4'])
        service.create_answer('q5', q_by_analysis_key['q5'])

        service.load_data()
        answers_by_analysis_key = service.get_answers_by_analysis_key()

        self.assertEqual(len(answers_by_analysis_key), 4)
        for key in ['q1', 'q2', 'q4', 'q5']:
            self.assertEqual(answers_by_analysis_key[key].payload, key)
