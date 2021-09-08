# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import networkx

from signals.apps.questionnaires.models import Answer, Edge, Question


class QuestionGraphService:
    MAX_QUESTIONS = 50

    def __init__(self, q_graph):
        self.q_graph = q_graph

    def load_question_data(self):
        # Retrieve all relevant edges, questions and answers
        self.edges = self._get_edges(self.q_graph)
        self.nx_graph = self._build_nx_graph(self.edges, self.q_graph.first_question)
        self.questions = self._get_all_questions(self.nx_graph)

        # setup caches for quick access
        self.edges_by_id = {e.id: e for e in self.edges}
        self.questions_by_id = {q.id: q for q in self.questions}

    def _get_edges(self, q_graph):
        return list(Edge.objects.filter(graph=q_graph).select_related('choice'))

    def _build_nx_graph(self, edges, first_question):
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

            if len(nx_graph) > self.MAX_QUESTIONS:
                msg = f'Question graph {self.graph.name} contains too many questions.'
                raise Exception(msg)

        if first_question and first_question not in nx_graph.nodes:
            nx_graph.add_node(first_question.id)
        return nx_graph

    def _get_all_questions(self, nx_graph):
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


class SessionService(QuestionGraphService):
    def __init__(self, session):
        super().__init__(session.questionnaire.graph)
        self.session = session

    def load_answer_data(self):
        self.answers = self._get_all_answers(self.session)
        self.answers_by_question_id = {a.question.id: a for a in self.answers}

        # Take into account QuestionGraph structure, determine questions,
        # unanswered questions and answers along path. Note that these paths
        # do not necessarily extend to the end of the questionnaire. (Only the
        # case if all decision points have a default branch that gets selected
        # without an answer being provided).
        # Note: call after _load_path_independent_data
        reachable, unanswered, answered, can_freeze = self._get_reachable_questions_and_answers(
            self.nx_graph, self.questions_by_id, self.answers_by_question_id
        )
        self.path_questions_by_id = reachable
        self.path_unanswered_by_id = unanswered
        self.path_answers_by_question_id = answered
        self.can_freeze = can_freeze

    def load_data(self):
        self.load_question_data()
        self.load_answer_data()

    def _get_all_answers(self, session):
        return list(
            Answer.objects.filter(session=session)
            .order_by('question_id', '-created_at')
            .distinct('question_id')
            .select_related('question')
        )

    def _get_next_question(self, nx_graph, questions_by_id, question, answer_payload):
        """
        Get next_question given question graph, current question, and answer.
        """
        # Retrieve outgoing edges, sort them so that the correct next_question
        # is selected (i.e. the match rules in correct order).
        out_edges = list(nx_graph.out_edges(question.id, data=True))
        out_edges.sort(key=lambda edge: (edge[2]['order'], edge[2]['edge_id']))

        # Try to match answer payload, retrieve correct question.
        for _, next_id, data in out_edges:
            choice_payload = data['choice_payload']
            if choice_payload is None or choice_payload == answer_payload:
                return questions_by_id[next_id]

        return None

    def _get_reachable_questions_and_answers(self, nx_graph, questions_by_id, answers_by_id):
        """
        Given (partially?) answered graph determine answers and questions along
        current path.
        """
        # We can assume that each individual answer is correct, we must now
        # determine whether these answers are reachable given relevant graph.
        reachable_answers_by_question_id = {}
        reachable_questions_by_id = {}
        unanswered_by_id = {}  # only (!) required questions left unanswered

        question = self.q_graph.first_question
        while question:
            reachable_questions_by_id[question.id] = question
            answer = answers_by_id.get(question.id, None)

            if not answer and question.required:
                unanswered_by_id[question.id] = question
            if answer is not None:
                reachable_answers_by_question_id[answer.question.id] = answer

            previous_question = question
            answer_payload = None if answer is None else answer.payload
            question = self._get_next_question(nx_graph, questions_by_id, question, answer_payload)

        can_freeze = False
        if nx_graph.out_degree(previous_question.id) == 0 and not unanswered_by_id:
            # We have reached a potential endpoint, and along our current path
            # there are no more questions to answer. This means session can be
            # frozen safely
            can_freeze = True

        return reachable_questions_by_id, unanswered_by_id, reachable_answers_by_question_id, can_freeze

    def _get_endpoint_questions(self, nx_graph, questions_by_id):
        """
        Get endpoint questions in QuestionGraph.
        """
        endpoint_questions_by_id = {}
        for question_id, out_degree in nx_graph.out_degree():
            if out_degree == 0:
                endpoint_questions_by_id[question_id] = questions_by_id[question_id]

        return endpoint_questions_by_id

    def get_answers_by_analysis_key(self):
        """
        Given (partially?) answered graph determine answers along current path.
        """
        # translate answers along path to dict keyed by question.analysis_key
        return {a.question.analysis_key: a for a in self.path_answers_by_question_id.values()}

    def get_extra_properties(self, category_url=None):
        """
        Given (partially?) answered graph determine answers along current path
        and return them in an Signal.extra_properties compatible dictionary.
        """
        # TODO: double check against VNG forms implementation
        # Translate answers along path to dict keyed by question.analysis_key
        # TBD, still how do we mark answers with the proper category
        extra_props = []
        for answer in self.path_answers_by_question_id.values():
            entry = {
                'id': answer.question.analysis_key,
                'label': answer.question.short_label,
                'answer': answer.payload,
            }
            if category_url:
                entry['category_url'] = category_url
            extra_props.append(entry)

        return extra_props

    def get_can_freeze(self):
        """
        Can the session under consideration be frozen (i.e. are all required
        questions answered)?
        """
        return self.can_freeze
