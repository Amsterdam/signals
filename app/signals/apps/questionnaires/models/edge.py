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
    choice = models.ForeignKey('Choice', on_delete=models.SET_NULL, related_name='+', null=True, blank=True)

    class Meta:
        ordering = ['order', 'id']
