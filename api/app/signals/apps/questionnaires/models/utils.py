# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import os

import matplotlib.pyplot as plt
import networkx
from django.utils import timezone
from networkx.drawing.nx_pydot import graphviz_layout

from signals.apps.questionnaires.services import QuestionGraphService

import pydot  # noqa


def draw_graph(question_graph, location=None):
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

    question_graph_service = QuestionGraphService(q_graph=question_graph)
    question_graph_service.load_question_graph_data()
    nx_graph = question_graph_service.nx_graph

    pos = graphviz_layout(nx_graph, prog='dot')
    networkx.draw(nx_graph, pos, labels=labels, font_size=10, node_color='lightblue')

    edge_labels = networkx.get_edge_attributes(nx_graph, 'choice_label')
    networkx.draw_networkx_edge_labels(nx_graph, pos=pos, edge_labels=edge_labels, label_pos=0.7, rotate=False,
                                       font_size=8)

    file_path = os.path.join(location, f'{now:%H%M%S}_graph-{question_graph.pk}.png')

    plt.savefig(file_path, format='png', bbox_inches='tight', )
    plt.close()

    return file_path
