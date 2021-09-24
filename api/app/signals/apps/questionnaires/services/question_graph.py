# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import networkx

from signals.apps.questionnaires.app_settings import MAX_QUESTIONS
from signals.apps.questionnaires.models import Edge, Question


class QuestionGraphService:
    def __init__(self, q_graph):
        self._q_graph = q_graph

    def refresh_from_db(self):
        # Retrieve all relevant edges, questions and answers
        self._edges = self._get_edges(self._q_graph)
        self._nx_graph = self._build_nx_graph(self._q_graph, self._edges)
        self._questions = self._get_all_questions(self._nx_graph)

        # setup caches for quick access
        self._edges_by_id = {e.id: e for e in self._edges}
        self._questions_by_id = {q.id: q for q in self._questions}

    def _get_edges(self, q_graph):
        return list(Edge.objects.filter(graph=q_graph).select_related('choice'))

    @staticmethod
    def _build_nx_graph(q_graph, edges):
        """
        Get NetworkX graph representing the QuestionGraph.
        """
        # To allow for matching rule and default rule (i.e. a double edge).
        nx_graph = networkx.MultiDiGraph()

        for edge in edges:
            # Needed for rule matching and dertermining next questions (edge
            # ordering is important if several rules match and we want
            # consistent results):
            edge_kwargs = {
                'choice_payload': None if edge.choice is None else edge.choice.payload,
                'edge_id': edge.id,
                'order': edge.order,
            }

            # Needed for question graph visualization:
            if edge.choice:
                edge_kwargs['choice_label'] = (f'{edge.choice.display or edge.choice.payload}'
                                               f' {" (selected)" if edge.choice.selected else ""}')

            # Add the edge with all relevant information:
            nx_graph.add_edge(edge.question_id, edge.next_question_id, **edge_kwargs)

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
        reachable = networkx.descendants(self._nx_graph, self._q_graph.first_question.id)
        reachable.add(self._q_graph.first_question.id)

        return list(Question.objects.filter(id__in=reachable))

    @property
    def nx_graph(self):
        if not hasattr(self, '_nx_graph'):
            self.refresh_from_db()
        return self._nx_graph

    @property
    def questions(self):
        if not hasattr(self, '_questions'):
            self.refresh_from_db()
        return self._questions

    @property
    def reachable_questions(self):
        if not hasattr(self, '_nx_graph'):
            self.refresh_from_db()

        reachable = networkx.descendants(self._nx_graph, self._q_graph.first_question.id)
        reachable.add(self._q_graph.first_question.id)
        return {q for q_id, q in self._questions_by_id.items() if q_id in reachable}

    def validate(self):
        """
        Check QuestionGraph for validity.
        """
        # TODO, check QuestionGraph for the following:
        # - maximum number of questions
        # - no unreachable questions
        # - decision points (questions) in the graph must enforce questions
        pass
