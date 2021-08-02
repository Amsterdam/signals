# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import uuid

import networkx
from django.contrib.gis.db import models
from django.db.models import DateTimeField, ExpressionWrapper, F, Q
from django.db.models.functions import Now


class QuestionManager(models.Manager):
    def get_by_reference(self, ref):
        """
        Retrieve question key or uuid (either can be the ref).
        """
        if ref is None:
            msg = 'Cannot get Question instance for ref=None'
            raise self.model.DoesNotExist(msg)

        try:
            return self.get(key=ref)
        except self.model.DoesNotExist:
            try:
                question_uuid = uuid.UUID(ref)
            except (ValueError, TypeError):
                raise self.model.DoesNotExist
            else:
                return self.get(uuid=question_uuid)

    def get_from_question_graph(self, question_graph):
        # TODO: do this query in ORM completely
        questions = set(question_graph.edges.values_list('question', flat=True))
        next_questions = set(question_graph.edges.values_list('next_question', flat=True))

        question_ids = questions | next_questions
        question_ids.add(question_graph.first_question_id)
        return self.filter(id__in=question_ids)

    def get_reachable_from_question_graph(self, question_graph):
        # Given the graph of questions:
        # - check that first_question is not None/null, otherwise return empty queryset
        # - retrieve all edges in one go (possibly do a count first and fail if too many ...)
        # - if there is a first question and there are no edges: return queryset with only first question
        # - construct a directed graph
        # - check that first question is a node in that graph, if not only return first question
        # - get the set of "descendants" of first question in the graph, turn it into a queryset and return it
        from signals.apps.questionnaires.models import Edge
        MAX_QUESTIONS = 50

        # No first question: return empty Question queryset
        if not question_graph.first_question:
            return self.none()

        # No edges: return Queryset with only the first question
        edges = Edge.objects.filter(graph=question_graph)
        if not edges.exists():
            return self.filter(id=question_graph.first_question_id)

        # first question and edges present, build directed graph
        nx_graph = networkx.DiGraph()
        for edge in edges:
            nx_graph.add_edge(edge.question_id, edge.next_question_id)
            if len(nx_graph) > MAX_QUESTIONS:
                msg = f'Question graph {question_graph.name} contains too many questions.'
                raise Exception(msg)

        # Our first_question should be part of the graph of questions, if it is
        # not only the first_question is reachable.
        if question_graph.first_question_id not in nx_graph:
            return self.filter(id=question_graph.first_question_id)

        # our question graph must be directed and acyclic
        if not networkx.is_directed_acyclic_graph(nx_graph):
            msg = f'Question graph {question_graph.name} not acyclic.'
            raise Exception(msg)

        # only questions reachable from the first_question node are of interest
        reachable = networkx.descendants(nx_graph, question_graph.first_question_id)
        reachable.add(question_graph.first_question_id)
        return self.filter(id__in=reachable)


class QuestionnaireManager(models.Manager):
    def active(self):
        """
        Returns only Questionnaires with the is_active set to True
        """
        return self.get_queryset().filter(is_active=True)


class SessionManager(models.Manager):
    def retrieve_valid_sessions(self):
        """
        Returns a queryset containing Sessions that fit one of the following conditions:

        * The submit_before is set and is still valid
        * The submit_before is NOT set, the Session is in use and the started_at + duration is still valid
        * The submit_before is NOT set and the Session is NOT in use

        And all of these conditions must only contain Sessions that are not frozen. Frozen sessions cannot be edited!
        """
        queryset = self.get_queryset()
        return queryset.annotate(
            # Calculate the submit before based on the started_at + duration
            submit_before_based_on_duration=ExpressionWrapper(
                F('started_at') + F('duration'),
                output_field=DateTimeField()
            )
        ).filter(
            (
                # All sessions that have a submit_before that has not yet passed
                (Q(submit_before__isnull=False) & Q(submit_before__gt=Now())) |
                # All sessions that do not have a submit_before but where the created_at + duration has not yet passed
                (Q(submit_before__isnull=True) & Q(submit_before_based_on_duration__gt=Now())) |
                # All sessions that have no submit_before and has not yet been answered
                (Q(submit_before__isnull=True) & Q(submit_before_based_on_duration__isnull=True))
            ),
            # Frozen session are not editable anymore
            frozen=False,
        ).all()
