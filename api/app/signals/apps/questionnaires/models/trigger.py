# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib.gis.db import models


class Trigger(models.Model):
    REOPEN_SIGNAL = 'reopen signal'
    ACTION_CHOICES = [
        (REOPEN_SIGNAL, 'Melding heropenen'),
    ]

    graph = models.ForeignKey('QuestionGraph', on_delete=models.CASCADE, related_name='action_triggers')
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='+')
    payload = models.JSONField(null=True, blank=True)  # <- validate using question field when saving

    order = models.IntegerField(default=0)  # Default is order of creation, can be overridden.

    action = models.CharField(max_length=255, choices=ACTION_CHOICES)
    arguments = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['order', 'id']
