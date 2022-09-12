# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
import logging
from collections import OrderedDict

from django.core.exceptions import ValidationError as django_validation_error
from django.utils import timezone

from signals.apps.questionnaires.exceptions import CycleDetected, SessionExpired, SessionFrozen
from signals.apps.questionnaires.models import Answer
from signals.apps.questionnaires.services.answer import AnswerService
from signals.apps.questionnaires.services.question_graph import QuestionGraphService

logger = logging.getLogger(__name__)


class SessionService:
    def __init__(self, session):
        self.session = session
        self.question_graph_service = QuestionGraphService(session.questionnaire.graph)
        self.answer_service = AnswerService
        self._path_validation_errors_by_uuid = {}

    def is_publicly_accessible(self):
        """
        Check whether the session associated with this SessionService is to be
        accessible through the public API. Will raise appropriate exceptions
        when the session must not be available.

        Note: flow specific implementations are in SessionService subclasses,
        these subclasses can use custom exception classes as well.
        """
        self.session.refresh_from_db()

        # Reaction was already provided (hence form filled out, and hence session.frozen):
        if self.session.frozen:
            raise SessionFrozen('Already used!')

        # Reaction was not provided in time and therefore this session expired:
        if self.session.is_expired:
            raise SessionExpired('Expired!')

    def load_session_data(self):
        self._answers = self._get_all_answers(self.session)
        self._answers_by_question_id = {a.question.id: a for a in self._answers}

        # Take into account QuestionGraph structure, determine questions,
        # unanswered questions and answers along path. Note that these paths
        # do not necessarily extend to the end of the questionnaire. (Only the
        # case if all decision points have a default branch that gets selected
        # without an answer being provided).
        reachable, unanswered, answered, can_freeze = self._get_reachable_questions_and_answers(
            self.question_graph_service._nx_graph,
            self.question_graph_service._q_graph.first_question,
            self.question_graph_service._questions_by_id,
            self._answers_by_question_id
        )
        self._path_questions_by_id = reachable
        self._path_unanswered_by_id = unanswered
        self._path_answers_by_question_id = answered
        self._can_freeze = can_freeze

    def refresh_from_db(self):
        self.session.refresh_from_db()
        self.question_graph_service.refresh_from_db()
        self.load_session_data()

    @staticmethod
    def _get_all_answers(session):
        """
        Get answers associated with this session, return only the most recent
        answer for each question.
        """
        return list(
            Answer.objects.filter(session=session)
            .order_by('question_id', '-created_at')
            .distinct('question_id')
            .select_related('question')
        )

    @staticmethod
    def _get_next_question(nx_graph, questions_by_id, question, answer_payload):
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

    @staticmethod
    def _get_reachable_questions_and_answers(nx_graph, first_question, questions_by_id, answers_by_id):
        """
        Given (partially?) answered graph determine answers and questions along
        current path.
        """
        # Assumptions:
        # - each individual answer is correct (previously validated)
        # - question graph has correct structure

        # We need to keep order of questions along path through question graph
        # hence the OrderedDict. Unanswered and required questions and answers
        # to questions along the path are also collected.
        reachable_questions_by_id = OrderedDict()
        reachable_answers_by_question_id = {}
        unanswered_by_id = {}  # Collect required questions left unanswered.

        question = first_question
        while question:
            # Protect against cycles in question graph:
            if question.id in reachable_questions_by_id:
                raise CycleDetected('Cycle detected')

            reachable_questions_by_id[question.id] = question
            answer = answers_by_id.get(question.id, None)

            if not answer and question.required:
                unanswered_by_id[question.id] = question
            if answer is not None:
                reachable_answers_by_question_id[answer.question.id] = answer

            previous_question = question
            answer_payload = None if answer is None else answer.payload
            question = SessionService._get_next_question(nx_graph, questions_by_id, question, answer_payload)

        # Finally we want to know whether session under consideration can be
        # frozen meaningfully (i.e. a path through it is fully answered and the
        # data can be made available for further processing).
        can_freeze = False
        if nx_graph.out_degree(previous_question.id) == 0 and not unanswered_by_id:
            # Endpoint reached (no outgoing edges) and no unanswered required questions.
            can_freeze = True

        return reachable_questions_by_id, unanswered_by_id, reachable_answers_by_question_id, can_freeze

    def get_next_question(self, question, answer):
        """
        Given question and its answer determine next question.
        """
        # TODO: consider removing when next_rules is removed from public API.
        return SessionService._get_next_question(
            self.question_graph_service._nx_graph,
            self.question_graph_service._questions_by_id,
            question,
            answer.payload
        )

    @property
    def answers_by_analysis_key(self):
        """
        Dictionary of answers along current path keyed by question analysis key.

        Note: for internal use, not over public API.
        """
        if not hasattr(self, '_path_answers_by_question_id'):
            self.refresh_from_db()

        return {a.question.analysis_key: a for a in self._path_answers_by_question_id.values()}

    @property
    def answers_by_question_uuid(self):
        """
        Dictionary of answers along current path keyed by question UUID.

        Note: for internal use, not over public API.
        """
        if not hasattr(self, '_path_answers_by_question_id'):
            self.refresh_from_db()

        return {a.question.uuid: a for a in self._path_answers_by_question_id.values()}

    def get_extra_properties(self, category_url=None):
        """
        Given (partially?) answered graph determine answers along current path
        and return them in an Signal.extra_properties compatible dictionary.
        """
        if not hasattr(self, '_path_answers_by_question_id'):
            self.refresh_from_db()

        # TODO: double check against VNG forms implementation
        # Translate answers along path to dict keyed by question.analysis_key
        # TBD, still how do we mark answers with the proper category
        extra_props = []
        for answer in self._path_answers_by_question_id.values():
            entry = self.answer_service.transform_to_extra_property(answer.payload, answer.question)
            if category_url:
                entry['category_url'] = category_url
            extra_props.append(entry)

        return extra_props

    def create_answer(self, answer_payload, question):
        """
        Answer a question, update session.started_at if needed.
        """
        if not hasattr(self, '_nx_graph'):
            self.refresh_from_db()

        # Check that question is actually part of relevant questionnaire:
        if question.id not in self.question_graph_service._nx_graph.nodes():
            msg = f'Question (id={question.id}) not in questionnaire (id={self.session.questionnaire.id})!'
            raise django_validation_error(msg)

        if not self.session.started_at:
            self.session.started_at = timezone.now()
            self.session.save()

        if self.session.is_expired:
            raise SessionExpired(f'Session {self.session.uuid} expired.')

        if self.session.frozen:
            raise SessionFrozen(f'Session {self.session.uuid} frozen.')

        # Check submitted answer validates. If so save it to DB and return it.
        self.answer_service.validate_answer_payload(answer_payload, question)

        answer = Answer.objects.create(session=self.session, question=question, payload=answer_payload)
        self.refresh_from_db()  # prevent stale data // TODO: consider only using load_session_data or updating cache
        return answer

    def create_answers(self, answer_payloads, questions):
        """
        Answer several questions, do not raise ValidationErrors instead save
        save a dictionary of errors keyed by question UUID on the SessionService
        (subclass).

        Note: to access the errors access the path_validation_errors property.
        """
        # We need all relevant data cached.
        if not hasattr(self, '_can_freeze'):
            self.refresh_from_db()

        # Iterate through answer payloads and questions, validate them, collect
        # any error (messages), and cache them on SessionService (subclass).
        errors_by_uuid = {}
        for answer_payload, question in zip(answer_payloads, questions):
            try:
                self.create_answer(answer_payload, question)
            except (SessionExpired, SessionFrozen) as e:
                # Expired sessions should raise not be possible to update
                raise e
            except django_validation_error as e:
                # For validation errors we keep the error messages
                errors_by_uuid[question.uuid] = e.message

        # Cache our validation errors so that these can be accessed through the
        # path_validation_errors property.
        self._path_validation_errors_by_uuid.update(errors_by_uuid)
        return errors_by_uuid

    @property
    def can_freeze(self):
        """
        Can this session be frozen given current answers.
        """
        if not hasattr(self, '_can_freeze'):
            self.refresh_from_db()
        return self._can_freeze

    @property
    def path_questions(self):
        """
        List of questions along current path.

        Note: current path may not extend to final question because of decision
        points in question graph. As these decision points (questions) get
        answered, the list of questions along current path may extend.
        """
        if not hasattr(self, '_path_answers_by_question_id'):
            self.refresh_from_db()

        return list(self._path_questions_by_id.values())

    @property
    def path_answered_question_uuids(self):
        """
        List of question UUIDs along current path that are answered.
        """
        # Note: by design no answers are returned here --- that may have
        # security/privacy implications. TODO: get input from privacy officer.
        # If we can send the answers back to the client, this would allow us
        # to fully synchronize the backend and client states (desirable).
        if not hasattr(self, '_path_answers_by_question_id'):
            self.refresh_from_db()

        return [a.question.uuid for a in self._path_answers_by_question_id.values()]

    @property
    def path_unanswered_question_uuids(self):
        """
        List of question UUIDs along current path that require an answer but
        have none.
        """
        if not hasattr(self, '_path_unanswered_by_id'):
            self.refresh_from_db()

        return [q.uuid for q in self._path_unanswered_by_id.values()]

    @property
    def path_validation_errors_by_uuid(self):
        """
        Dictionary of validation error messages keyed by Question UUID.
        """
        if not hasattr(self, '_path_validation_errors_by_uuid'):
            # This property is only set when answer_payloads were processed, if
            # that was not the case we cannot just call self.refresh_from_db()
            # because we have no access to answer payloads here. In this case
            # we just return an empty validation errors dictionary.
            return {}
        return self._path_validation_errors_by_uuid

    def freeze(self):
        """
        Freeze the Session.

        Note: this should be overridden by SessionService subclasses to add
        custom session processing.
        """
        self.session.frozen = True
        self.session.save()
