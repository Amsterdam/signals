# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from signals.apps.questionnaires.models import Edge, Question
from signals.apps.questionnaires.rest_framework.fields import QuestionHyperlinkedIdentityField
from signals.apps.questionnaires.rest_framework.serializers.public.illustrated_text import (
    NestedPublicIllustratedTextSerializer
)


class PublicQuestionSerializer(HALSerializer):
    serializer_url_field = QuestionHyperlinkedIdentityField
    next_rules = serializers.SerializerMethodField()
    _display = DisplayField()
    key = serializers.CharField(source='retrieval_key')
    explanation = NestedPublicIllustratedTextSerializer()

    class Meta:
        model = Question
        fields = (
            '_links',
            '_display',
            'key',
            'retrieval_key',
            'analysis_key',
            'uuid',
            'label',
            'short_label',
            'field_type',
            'next_rules',
            'required',
            'explanation',
        )
        read_only_fields = fields  # No create or update allowed

    def get_next_rules(self, obj):
        # For backwards compatibility with earlier REST API version, this is
        # candidate for removal. This also only makes sense for questions seen
        # as part of a QuestionGraph, as the next_rules are no longer on the
        # Question object --- graph structure is now explicitly modelled in the
        # QuestionGraph and Edge objects.
        next_rules = None
        if graph := self.context.get('graph', None):
            outgoing_edges = Edge.objects.filter(graph=graph, question=obj)

            next_rules = []
            for edge in outgoing_edges:
                payload = edge.choice.payload if edge.choice else None
                next_rules.append({'key': edge.next_question.ref, 'payload': payload})

        return next_rules


class PublicQuestionDetailedSerializer(PublicQuestionSerializer):
    pass
