# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.test import TestCase
from networkx import MultiDiGraph

from signals.apps.questionnaires.services.question_graph import QuestionGraphService
from signals.apps.questionnaires.tests.test_models import create_diamond_plus


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

        service.load_question_graph_data()
        self.assertEqual(len(service.edges), 6)
        self.assertIsInstance(service.nx_graph, MultiDiGraph)
        self.assertEqual(len(service.nx_graph.nodes), 7)
        self.assertEqual(len(service.questions), 7)
        self.assertEqual(len(service.questions_by_id), 7)
