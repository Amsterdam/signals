# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import os

import matplotlib.pyplot as plt
import networkx
from django.utils import timezone
from networkx.drawing.nx_pydot import graphviz_layout

import pydot  # noqa


def make_nx_graph(question_graph):
    nx_graph = networkx.DiGraph()
    nx_graph.add_node(question_graph.first_question_id)
    for edge in question_graph.edges.all():
        if edge.choice:
            choice_label = f'{edge.choice.display or edge.choice.payload}' \
                           f'{" (selected)" if edge.choice.selected else ""}'
        else:
            choice_label = ''

        nx_graph.add_edge(edge.question_id, edge.next_question_id, choice_label=choice_label)

    return nx_graph


def validate_nx_graph(question_graph):
    nx_graph = make_nx_graph(question_graph)
    if len(nx_graph) > question_graph.MAX_QUESTIONS_PER_GRAPH:
        raise Exception(f'Question graph {question_graph.name} contains too many questions.')

    if not networkx.is_directed_acyclic_graph(nx_graph):
        raise Exception(f'Question graph {question_graph.name} is cyclic.')

    return nx_graph


def retrieve_reachable_questions(question_graph):
    # Given the graph of questions:
    # - check that first_question is not None/null, otherwise return empty queryset
    # - retrieve all edges in one go (possibly do a count first and fail if too many ...)
    # - if there is a first question and there are no edges: return queryset with only first question
    # - construct a directed graph
    # - check that first question is a node in that graph, if not only return first question
    # - get the set of "descendants" of first question in the graph, turn it into a queryset and return it
    from signals.apps.questionnaires.models import Question

    if not question_graph.first_question:
        return Question.objects.none()

    if not question_graph.edges.exists():
        return Question.objects.filter(pk=question_graph.first_question_id)

    nx_graph = validate_nx_graph(question_graph)

    reachable = networkx.descendants(nx_graph, question_graph.first_question_id)
    reachable.add(question_graph.first_question_id)
    return Question.objects.filter(pk__in=reachable)


def draw_graph(question_graph, location='/'):
    from signals.apps.questionnaires.models import Question

    now = timezone.now()

    question_ids = list(
        question_graph.edges.values_list('next_question_id', flat=True)
    ) + [question_graph.first_question.id]
    question_qs = Question.objects.filter(id__in=question_ids)

    labels = {
        question.id: question.id
        for question in question_qs
    }

    nx_graph = make_nx_graph(question_graph)

    pos = graphviz_layout(nx_graph, prog='dot')
    networkx.draw(nx_graph, pos, labels=labels, font_size=10, node_color='lightblue')

    edge_labels = networkx.get_edge_attributes(nx_graph, 'choice_label')
    networkx.draw_networkx_edge_labels(nx_graph, pos=pos, edge_labels=edge_labels, label_pos=0.7, rotate=False,
                                       font_size=8)

    file_path = os.path.join(location, f'{now:%H%M%S}_graph-{question_graph.pk}.png')

    plt.savefig(file_path, format='png', bbox_inches='tight', )
    plt.close()

    return file_path
