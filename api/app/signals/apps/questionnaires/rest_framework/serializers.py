# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework.exceptions import ValidationError

from signals.apps.questionnaires.models import Answer, Question, Questionnaire, Session
from signals.apps.questionnaires.rest_framework.fields import (
    EmptyHyperlinkedIdentityField,
    QuestionHyperlinkedIdentityField,
    QuestionnairePrivateHyperlinkedIdentityField,
    QuestionnairePublicHyperlinkedIdentityField,
    SessionPublicHyperlinkedIdentityField,
    UUIDRelatedField
)
from signals.apps.questionnaires.services import QuestionnairesService


class PublicQuestionSerializer(HALSerializer):
    serializer_url_field = QuestionHyperlinkedIdentityField
    _display = DisplayField()

    class Meta:
        model = Question
        fields = (
            '_links',
            '_display',
            'key',
            'uuid',
            'field_type',
            'payload',
            'required',
        )
        read_only_fields = fields  # No create or update allowed


class PublicQuestionDetailedSerializer(PublicQuestionSerializer):
    pass


class PrivateQuestionSerializer(HALSerializer):
    serializer_url_field = QuestionHyperlinkedIdentityField
    _display = DisplayField()

    class Meta:
        model = Question
        fields = (
            '_links',
            '_display',
            'id',
            'key',
            'uuid',
            'field_type',
            'payload',
            'required',
            'created_at',
        )
        read_only_fields = (
            'id',
            'uuid',
            'created_at',
        )


class PrivateQuestionDetailedSerializer(PrivateQuestionSerializer):
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


class PrivateQuestionnaireSerializer(HALSerializer):
    serializer_url_field = QuestionnairePrivateHyperlinkedIdentityField

    _display = DisplayField()
    first_question = PrivateQuestionSerializer()

    class Meta:
        model = Questionnaire
        fields = (
            '_links',
            '_display',
            'id',
            'uuid',
            'name',
            'description',
            'is_active',
            'created_at',
            'first_question'
        )
        read_only_fields = (
            'id',
            'uuid',
            'created_at',
        )


class PrivateQuestionnaireDetailedSerializer(PrivateQuestionnaireSerializer):
    first_question = PrivateQuestionDetailedSerializer()


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
            questionnaire = session.questionnaire
        else:
            session = None
            questionnaire = validated_data.pop('questionnaire')

        return QuestionnairesService.create_answer(
            answer_payload=payload, question=question, questionnaire=questionnaire, session=session
        )
