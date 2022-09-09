# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
"""
QuestionGraph service contains functionality that deals with QuestionGraph
structure (reachable questions and the like).
"""
import networkx

from signals.apps.questionnaires.app_settings import MAX_QUESTIONS
from signals.apps.questionnaires.models import Edge, Question


class QuestionGraphService:
    def __init__(self, q_graph):
        self._q_graph = q_graph

    def refresh_from_db(self):
        """
        Retrieve all QuestionGraph data, cache it.
        """
        # Retrieve all relevant edges, questions and answers
        self._edges = self._get_edges(self._q_graph)
        self._nx_graph = self._build_nx_graph(self._q_graph, self._edges)
        self._questions = self._get_all_questions(self._nx_graph)

        # setup caches for quick access
        self._edges_by_id = {e.id: e for e in self._edges}
        self._questions_by_id = {q.id: q for q in self._questions}

        self._reachable_questions_by_id = self._get_reachable_questions(self._nx_graph, self._q_graph)
        self._endpoint_questions_by_id = self._get_endpoint_questions(
            self._nx_graph, self._questions_by_id, self._reachable_questions_by_id)

    def _get_edges(self, q_graph):
        """
        List of Edge instances decsribing QuestionGraph structure.
        """
        return list(Edge.objects.filter(graph=q_graph)
                                .select_related('choice')
                                .select_related('question')
                                .select_related('next_question'))

    @staticmethod
    def _build_nx_graph(q_graph, edges):
        """
        Get NetworkX graph representing the QuestionGraph.
        """
        # To allow for matching rule and default rule (i.e. a double edge).
        nx_graph = networkx.MultiDiGraph()

        for edge in edges:
            # Needed for rule matching and determining next questions (edge
            # ordering is important if several rules match and we want
            # consistent results):
            edge_kwargs = {
                'choice_payload': None if edge.choice is None else edge.choice.payload,
                'choice_payload_display': '' if edge.choice is None else edge.choice.display,
                'edge_id': edge.id,
                'order': edge.order,
            }

            # Needed for question graph visualization:
            if edge.choice:
                edge_kwargs['choice_label'] = (f'{edge.choice.display or edge.choice.payload}'
                                               f' {" (selected)" if edge.choice.selected else ""}')

            # Add the edge with all relevant information:
            nx_graph.add_edge(edge.question_id, edge.next_question_id, **edge_kwargs)

            # Add node metadata
            nx_graph.add_node(edge.question.id, label=edge.question.label, ref=edge.question.ref,
                              multiple_answers_allowed=edge.question.multiple_answers_allowed)
            nx_graph.add_node(edge.next_question.id, label=edge.next_question.label, ref=edge.next_question.ref)

            if len(nx_graph) > MAX_QUESTIONS:
                msg = f'Question graph {q_graph.name} contains too many questions.'
                raise Exception(msg)

        if q_graph.first_question and q_graph.first_question not in nx_graph.nodes:
            nx_graph.add_node(q_graph.first_question.id, label=q_graph.first_question.label,
                              ref=q_graph.first_question.ref,
                              multiple_answers_allowed=q_graph.first_question.multiple_answers_allowed)

        return nx_graph

    @staticmethod
    def _get_reachable_questions(nx_graph, q_graph):
        """
        Grab questions linked to QuestionGraph reachable from first_question.
        """
        reachable = networkx.descendants(nx_graph, q_graph.first_question.id)
        reachable.add(q_graph.first_question.id)

        return {q.id: q for q in Question.objects.filter(id__in=reachable)}

    @staticmethod
    def _get_endpoint_questions(nx_graph, questions_by_id, reachable_questions_by_id):
        """
        Get endpoint questions in QuestionGraph.
        """
        endpoint_questions_by_id = {}
        for question_id, out_degree in nx_graph.out_degree():
            if out_degree == 0 and question_id in reachable_questions_by_id:
                endpoint_questions_by_id[question_id] = questions_by_id[question_id]

        return endpoint_questions_by_id

    @staticmethod
    def _get_all_questions(nx_graph):
        """
        Grab questions linked to QuestionGraph.
        """
        return list(Question.objects.filter(id__in=nx_graph.nodes()))

    @property
    def endpoint_questions(self):
        """
        List of questions that form the endpoints of a QuestionGraph.
        """
        if not hasattr(self, '_endpoint_questions_by_id'):
            self.refresh_from_db()
        return self._endpoint_questions_by_id

    @property
    def nx_graph(self):
        """
        networkx.MultiDigraph instance representing QuestionGraph.
        """
        if not hasattr(self, '_nx_graph'):
            self.refresh_from_db()
        return self._nx_graph

    @property
    def questions(self):
        """
        List of Question instance (reachable and not) for QuestionGraph.
        """
        if not hasattr(self, '_questions'):
            self.refresh_from_db()
        return self._questions

    @property
    def reachable_questions(self):
        """
        List of Question instances for QuestionGraph (only reachable ones).
        """
        if not hasattr(self, '_reachable_questions_by_id'):
            self.refresh_from_db()
        return list(self._reachable_questions_by_id.values())

    def validate(self):
        """
        Check QuestionGraph for validity.
        """
        # TODO, check QuestionGraph for the following:
        # - maximum number of questions
        # - no unreachable questions
        # - decision points (questions) in the graph must enforce questions
        pass
