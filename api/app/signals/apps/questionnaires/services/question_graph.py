# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import networkx

from signals.apps.questionnaires.app_settings import MAX_QUESTIONS
from signals.apps.questionnaires.models import Edge, Question


class QuestionGraphService:
    def __init__(self, q_graph):
        self.q_graph = q_graph

    def load_question_graph_data(self):
        # Retrieve all relevant edges, questions and answers
        self.edges = self._get_edges(self.q_graph)
        self.nx_graph = self._build_nx_graph(self.q_graph, self.edges)
        self.questions = self._get_all_questions(self.nx_graph)

        # setup caches for quick access
        self.edges_by_id = {e.id: e for e in self.edges}
        self.questions_by_id = {q.id: q for q in self.questions}

    def _get_edges(self, q_graph):
        return list(Edge.objects.filter(graph=q_graph).select_related('choice'))

    @staticmethod
    def _build_nx_graph(q_graph, edges):
        """
        Get NetworkX graph representing the QuestionGraph.
        """
        nx_graph = networkx.MultiDiGraph()
        for edge in edges:
            choice_payload = None if edge.choice is None else edge.choice.payload

            nx_graph.add_edge(
                edge.question_id,
                edge.next_question_id,
                # Needed for rule matching and dertermining next questions:
                choice_payload=choice_payload,
                edge_id=edge.id,
                order=edge.order,
            )

            if len(nx_graph) > MAX_QUESTIONS:
                msg = f'Question graph {q_graph.name} contains too many questions.'
                raise Exception(msg)

        if q_graph.first_question and q_graph.first_question not in nx_graph.nodes:
            nx_graph.add_node(q_graph.first_question.id)
        return nx_graph

    @staticmethod
    def _get_all_questions(nx_graph):
        """
        Grab questions linked to QuestionGraph.
        """
        return list(Question.objects.filter(id__in=nx_graph.nodes()))

    def get_all_questions(self):
        return self.questions

    def get_reachable_questions(self):
        """
        Grab questions linked to QuestionGraph reachable from first_question.
        """
        reachable = networkx.descendants(self.nx_graph, self.q_graph.first_question.id)
        reachable.add(self.q_graph.first_question.id)

        return list(Question.objects.filter(id__in=reachable))

    def validate(self):
        """
        Check QuestionGraph for validity.
        """
        # TODO, check QuestionGraph for the following:
        # - maximum number of questions
        # - no unreachable questions
        # - decision points (questions) in the graph must enforce questions
        pass
