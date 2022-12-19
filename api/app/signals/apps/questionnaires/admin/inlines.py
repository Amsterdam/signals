# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib.admin.options import StackedInline
from django.contrib.gis.db.models import JSONField

from signals.apps.api.forms.widgets import PrettyJSONWidget
from signals.apps.questionnaires.admin.options import NonRelatedStackedInline
from signals.apps.questionnaires.models import Choice, Edge, QuestionGraph, Questionnaire


class EdgeStackedInline(NonRelatedStackedInline):
    model = Edge
    fields = ('question', 'next_question', 'order', 'choice',)

    extra = 1
    formfield_overrides = {JSONField: {'widget': PrettyJSONWidget}}

    def get_form_queryset(self, obj):
        if isinstance(obj, Questionnaire):
            return self.model.objects.filter(graph=obj.graph) if obj.graph else self.model.objects.all()
        elif isinstance(obj, QuestionGraph):
            return self.model.objects.filter(graph=obj) if obj else self.model.objects.all()
        return self.model.objects.none()

    def save_new_instance(self, parent, instance):
        if isinstance(parent, Questionnaire):
            instance.graph = parent.graph
        elif isinstance(parent, QuestionGraph):
            instance.graph = parent


class ChoiceStackedInline(StackedInline):
    model = Choice

    fields = ('question', 'display', 'selected', 'payload',)

    extra = 1
    formfield_overrides = {JSONField: {'widget': PrettyJSONWidget}}
