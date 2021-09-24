# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.questionnaires.models import Answer, Edge, Question, Questionnaire, Session
from signals.apps.questionnaires.rest_framework.fields import (
    EmptyHyperlinkedIdentityField,
    QuestionHyperlinkedIdentityField,
    QuestionnairePublicHyperlinkedIdentityField,
    SessionPublicHyperlinkedIdentityField,
    UUIDRelatedField
)
from signals.apps.questionnaires.services.utils import get_session_service


class PublicQuestionSerializer(HALSerializer):
    serializer_url_field = QuestionHyperlinkedIdentityField
    next_rules = serializers.SerializerMethodField()
    _display = DisplayField()
    key = serializers.CharField(source='retrieval_key')

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


class PublicQuestionnaireSerializer(HALSerializer):
    serializer_url_field = QuestionnairePublicHyperlinkedIdentityField

    _display = DisplayField()
    first_question = PublicQuestionSerializer()

    class Meta:
        model = Questionnaire
        fields = (
            '_links',
            '_display',
            'uuid',
            'name',
            'description',
            'is_active',
            'first_question'
        )
        read_only_fields = fields  # No create or update allowed


class PublicQuestionnaireDetailedSerializer(PublicQuestionnaireSerializer):
    first_question = PublicQuestionDetailedSerializer()


class PublicSessionSerializer(HALSerializer):
    serializer_url_field = SessionPublicHyperlinkedIdentityField

    _display = DisplayField()

    class Meta:
        model = Session
        fields = (
            '_links',
            '_display',
            'uuid',
            'started_at',
            'submit_before',
            'duration',
            'created_at',
        )
        read_only_fields = (
            'id',
            'uuid',
            'created_at',
        )


class PublicSessionDetailedSerializer(PublicSessionSerializer):
    pass


class PublicAnswerSerializer(HALSerializer):
    serializer_url_field = EmptyHyperlinkedIdentityField

    _display = DisplayField()

    session = UUIDRelatedField(uuid_field='uuid', queryset=Session.objects.retrieve_valid_sessions(), required=False)
    questionnaire = UUIDRelatedField(uuid_field='uuid', queryset=Questionnaire.objects.active(), required=False)

    class Meta:
        model = Answer
        fields = (
            '_links',
            '_display',
            'payload',
            'session',
            'questionnaire',
            'created_at',
        )
        read_only_fields = (
            'created_at',
        )

    def validate(self, attrs):
        attrs = super(PublicAnswerSerializer, self).validate(attrs=attrs)

        if 'session' in attrs and 'questionnaire' in attrs:
            raise ValidationError('session and questionnaire cannot be used both!')
        elif 'session' not in attrs and 'questionnaire' not in attrs:
            raise ValidationError('Either the session or questionnaire is mandatory!')

        # TODO: Add a check to see if the question belongs to the questionnaire that is being processed

        return attrs

    def create(self, validated_data):
        question = self.context['question']
        payload = validated_data.pop('payload')

        if 'session' in validated_data:
            session = validated_data.pop('session')
            session_service = get_session_service(session)
        else:
            questionnaire = validated_data.pop('questionnaire')
            session = Session.objects.create(questionnaire=questionnaire)
            session_service = get_session_service(session)

        session_service.refresh_from_db()
        return session_service.create_answer(payload, question)
