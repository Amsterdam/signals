# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib.gis.db import models


class Edge(models.Model):
    """
    Edges store the rules that are used to get from one question to the next.
    """

    graph = models.ForeignKey('QuestionGraph', on_delete=models.CASCADE, related_name='edges')

    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='+')
    next_question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='+')

    order = models.IntegerField(default=0)  # Default is order of creation, can be overridden.
    payload = models.JSONField(null=True, blank=True)  # <- validate using question field when saving

    class Meta:
        ordering = ['order', 'id']
