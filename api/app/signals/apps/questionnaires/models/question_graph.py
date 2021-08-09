# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib.gis.db import models

from signals.apps.questionnaires.models.edge import Edge


class QuestionGraph(models.Model):
    """
    QuestionGraph models the structure of a questionnaire as a graph.

    The nodes in that graph are Question instances and the edges are Edge
    instances.
    """
    name = models.CharField(max_length=255, unique=True)
    first_question = models.ForeignKey('Question', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')

    def get_edges(self, question):
        return Edge.objects.filter(graph=self, question=question)

    def get_edge_order(self, question):
        return Edge.objects.filter(graph=self, question=question).values_list('id', flat=True)

    def set_edge_order(self, question, ids):
        all_ids = set(Edge.objects.filter(graph=self, question=question).values_list('id', flat=True))
        if set(ids) != all_ids:
            msg = 'Cannot update edge order, edge ids are not correct.'
            raise Exception(msg)

        for i, id_ in enumerate(ids):
            edge = Edge.objects.get(id=id_)
            edge.order = i
            edge.save()

        return Edge.objects.filter(graph=self, question=question).values_list('id', flat=True)
