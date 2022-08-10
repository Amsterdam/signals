# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from django.contrib.gis.db import models

from signals.apps.questionnaires.models.edge import Edge
from signals.apps.questionnaires.models.trigger import Trigger


class QuestionGraph(models.Model):
    """
    QuestionGraph models the structure of a questionnaire as a graph.

    The nodes in that graph are Question instances and the edges are Edge
    instances.
    """
    name = models.CharField(max_length=255, blank=True, null=True)
    first_question = models.ForeignKey('Question', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')

    def _set_model_order(self, question, model, ids):
        all_ids = set(model.objects.filter(graph=self, question=question).values_list('id', flat=True))
        if set(ids) != all_ids or len(ids) != len(all_ids):
            msg = f'Cannot update {model.__name__} order, {model.__name__} instance ids are not correct.'
            raise Exception(msg)

        for i, id_ in enumerate(ids):
            instance = model.objects.get(id=id_)
            instance.order = i
            instance.save()

        return model.objects.filter(graph=self, question=question).values_list('id', flat=True)

    def get_nodes(self):
        nodes = {}
        seen = set()

        for edge in Edge.objects.filter(graph=self):
            if edge.question_id not in seen:
                seen.add(edge.question_id)
                nodes.update({edge.question.id: edge.question})
            if edge.next_question_id not in seen:
                seen.add(edge.next_question_id)
                nodes.update({edge.next_question.id: edge.next_question})

        if self.first_question_id not in seen:
            nodes.update({self.first_question.id: self.first_question})
        return nodes

    def get_edges(self, question):
        return Edge.objects.filter(graph=self, question=question)

    def get_edge_order(self, question):
        return Edge.objects.filter(graph=self, question=question).values_list('id', flat=True)

    def set_edge_order(self, question, ids):
        return self._set_model_order(question, Edge, ids)

    def get_triggers(self, question):
        return Trigger.objects.filter(graph=self, question=question)

    def get_trigger_order(self, question):
        return Trigger.objects.filter(graph=self, question=question).values_list('id', flat=True)

    def set_trigger_order(self, question, ids):
        return self._set_model_order(question, Trigger, ids)
