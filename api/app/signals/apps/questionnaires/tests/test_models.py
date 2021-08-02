# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Test models and associated manager functions for the questionnaires app.
"""
import uuid

from django.test import TestCase

from signals.apps.questionnaires.factories import EdgeFactory, QuestionFactory, QuestionGraphFactory
from signals.apps.questionnaires.models import Edge, Question, QuestionGraph


def create_diamond(graph_name='diamond'):
    """
    Seed the database with a diamond shaped graph formed by questions.
    """
    q1 = QuestionFactory.create()
    q2 = QuestionFactory.create()
    q3 = QuestionFactory.create()
    q4 = QuestionFactory.create()
    q5 = QuestionFactory.create()

    # sketch:
    #    q1 <- first_question
    #   /  \
    # q2    q3
    #   \  /
    #    q4
    #    |
    #    q5
    graph = QuestionGraphFactory.create(name=graph_name, first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q2, payload=None)
    EdgeFactory.create(graph=graph, question=q2, next_question=q4, payload=None)
    EdgeFactory.create(graph=graph, question=q1, next_question=q3, payload=None)
    EdgeFactory.create(graph=graph, question=q3, next_question=q4, payload=None)
    EdgeFactory.create(graph=graph, question=q4, next_question=q5, payload=None)

    return graph


def create_diamond_plus(graph_name='diamond_plus'):
    graph = create_diamond(graph_name='diamond_plus')
    # sketch:
    #    q1 <- first_question
    #   /  \
    # q2    q3
    #   \  /
    #    q4     q6
    #    |      |
    #    q5     q7

    # Add an edge to the graph that cannot be reached from the first
    # question of the question_graph
    q6 = QuestionFactory.create()
    q7 = QuestionFactory.create()
    EdgeFactory.create(graph=graph, question=q6, next_question=q7, payload=None)


def create_empty(graph_name='empty'):
    return QuestionGraphFactory.create(name=graph_name, first_question=None)


def create_one(graph_name='one'):
    q1 = QuestionFactory.create()
    # sketch:
    # q1 <- first_question
    return QuestionGraphFactory.create(name=graph_name, first_question=q1)


def create_disconnected(graph_name='disconnected'):
    q1 = QuestionFactory.create()
    q2 = QuestionFactory.create()
    q3 = QuestionFactory.create()

    # sketch:
    # q1 <- first_question
    #
    # q2
    # |
    # q3
    graph = QuestionGraphFactory.create(name=graph_name, first_question=q1)
    EdgeFactory.create(graph=graph, question=q2, next_question=q3, payload=None)

    return graph


def create_cycle(graph_name='cycle'):
    q1 = QuestionFactory.create()
    q2 = QuestionFactory.create()

    # sketch:
    #  q1 <- first_question
    # (  )
    #  q2
    graph = QuestionGraphFactory.create(name=graph_name, first_question=q1)
    EdgeFactory(graph=graph, question=q1, next_question=q2, payload=None)
    EdgeFactory(graph=graph, question=q2, next_question=q1, payload=None)

    return graph


def create_too_many_questions(graph_name='too_many'):
    questions = [QuestionFactory.create() for i in range(100)]  # TODO: make MAX_QUESTIONS an app setting

    graph = QuestionGraphFactory.create(name=graph_name, first_question=questions[0])
    for i in range(len(questions) - 1):
        EdgeFactory.create(graph=graph, question=questions[i], next_question=questions[i + 1])

    return graph


class TestEmpty(TestCase):
    def setUp(self):
        create_empty()

    def test_get_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='empty')
        self.assertEqual(len(question_graph.edges.all()), 0)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 0)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='empty')

        questions = Question.objects.get_reachable_from_question_graph(question_graph)
        self.assertEqual(len(questions), 0)


class TestOne(TestCase):
    def setUp(self):
        create_one()

    def test_get_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='one')
        self.assertEqual(len(question_graph.edges.all()), 0)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 1)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='one')

        questions = Question.objects.get_reachable_from_question_graph(question_graph)
        self.assertEqual(len(questions), 1)


class TestDiamond(TestCase):
    def setUp(self):
        create_diamond()

    def test_get_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='diamond')
        self.assertEqual(len(question_graph.edges.all()), 5)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 5)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='diamond')
        questions = Question.objects.get_reachable_from_question_graph(question_graph)
        self.assertEqual(len(questions), 5)


class TestDiamondPlus(TestCase):
    def setUp(self):
        create_diamond_plus()

    def test_get_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='diamond_plus')
        self.assertEqual(len(question_graph.edges.all()), 5 + 1)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 7)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='diamond_plus')

        questions = Question.objects.get_reachable_from_question_graph(question_graph)
        self.assertEqual(len(questions), 5)

        self.assertEqual(Question.objects.count(), 7)
        self.assertEqual(Edge.objects.count(), 6)


class TestDisconnected(TestCase):
    def setUp(self):
        create_disconnected()

    def test_get_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='disconnected')
        self.assertEqual(len(question_graph.edges.all()), 1)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 3)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='disconnected')

        questions = Question.objects.get_reachable_from_question_graph(question_graph)
        self.assertEqual(len(questions), 1)

        self.assertEqual(Question.objects.count(), 3)
        self.assertEqual(Edge.objects.count(), 1)


class TestCycle(TestCase):
    def setUp(self):
        create_cycle()

    def test_get_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='cycle')
        self.assertEqual(len(question_graph.edges.all()), 2)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 2)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='cycle')

        with self.assertRaises(Exception) as e:
            Question.objects.get_reachable_from_question_graph(question_graph)
            self.assertIn('not acyclic', str(e))


class TestTooMany(TestCase):
    def setUp(self):
        create_too_many_questions()

    def test_get_from_question_graph(self):
        # TODO: consider whether we want to raise an error in QuestionManager.get_from_question_graph in case too many
        # questions are added to the graph.
        question_graph = QuestionGraph.objects.get(name='too_many')
        self.assertEqual(len(question_graph.edges.all()), 99)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 100)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='too_many')

        with self.assertRaises(Exception) as e:
            Question.objects.get_reachable_from_question_graph(question_graph)
            self.assertIn('too many', str(e))


class TestEdgeOrdering(TestCase):
    def setUp(self):
        #    q1
        #   / | \
        #  q2 q3 q4
        q1 = QuestionFactory.create()
        q2 = QuestionFactory.create()
        q3 = QuestionFactory.create()
        q4 = QuestionFactory.create()

        self.graph = QuestionGraphFactory.create(name='order',  first_question=q1)
        EdgeFactory.create(graph=self.graph, question=q1, next_question=q2, payload=None)
        EdgeFactory.create(graph=self.graph, question=q1, next_question=q3, payload=None)
        EdgeFactory.create(graph=self.graph, question=q1, next_question=q4, payload=None)

    def test_edge_ordering(self):
        question = self.graph.first_question
        before = self.graph.get_edge_order(question)
        for id_, edge in zip(before, self.graph.get_edges(question)):
            self.assertEqual(id_, edge.id)

        # now reorder our edges
        change = before[1:] + before[:1]
        after = self.graph.set_edge_order(question, change)
        for id_, edge in zip(after, self.graph.get_edges(question)):
            self.assertEqual(id_, edge.id)


class TestGetByReference(TestCase):
    def setUp(self):
        self.question = QuestionFactory.create(key='question')

    def test_get_by_reference_none(self):
        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get_by_reference(None)

    def test_get_by_reference_key(self):
        question = Question.objects.get_by_reference('question')
        self.assertEqual(self.question, question)

        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get_by_reference('NO SUCH QUESTION')

    def test_get_by_reference_uuid(self):
        question = Question.objects.get_by_reference(str(self.question.uuid))
        self.assertEqual(question, self.question)

        generated = uuid.uuid4()
        while generated == self.question.uuid:
            generated = uuid.uuid4()

        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get_by_reference(str(generated))

    def test_pathological_case_key_is_valid_uuid(self):
        # Set up a question that has a valid UUID as a key, make sure that
        # that one UUID does not match the question's `uuid` property.
        question = QuestionFactory.create()

        generated = uuid.uuid4()
        while generated == question.uuid:
            generated = uuid.uuid4()

        question.key = generated
        question.save()
        question.refresh_from_db()

        # TODO: fix behavior of get_by_reference triggered below (hence the
        # test is marged as an expected failure)
        retrieved = Question.objects.get_by_reference(str(generated))
        self.assertEqual(retrieved, question)