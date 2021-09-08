# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib.gis.db import models
from django.utils.safestring import mark_safe

from signals.apps.questionnaires.models.edge import Edge
from signals.apps.questionnaires.models.trigger import Trigger


class QuestionGraph(models.Model):
    """
    QuestionGraph models the structure of a questionnaire as a graph.

    The nodes in that graph are Question instances and the edges are Edge
    instances.
    """
    MAX_QUESTIONS_PER_GRAPH = 50

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

    @property
    def reachable_questions(self):
        from signals.apps.questionnaires.models.utils import retrieve_reachable_questions
        return retrieve_reachable_questions(self)

    def draw(self, location='/'):
        from signals.apps.questionnaires.models.utils import draw_graph
        return draw_graph(self, location=location)

    def draw_base64(self):
        """
        Image as base64 encoded string
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(self.draw(location=tmp_dir), "rb") as img_file:
                import base64
                return base64.b64encode(img_file.read()).decode("utf-8")

    @mark_safe
    def image_tag(self):
        """
        This function will return an image tag with a bas64 encoded image of the Graph.
        Used to show a visual representation of the Graph in the Django admin.
        """
        return f'<img src="data:image/png;base64, {self.draw_base64()}" />'
    image_tag.short_description = 'Visual representation'
    image_tag.allow_tags = True
