# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.rest import DisplayField, HALSerializer

from signals.apps.questionnaires.fields import (
    QuestionHyperlinkedIdentityField,
    QuestionnairePrivateHyperlinkedIdentityField,
    QuestionnairePublicHyperlinkedIdentityField,
    SessionPublicHyperlinkedIdentityField,
)
from signals.apps.questionnaires.models import Question, Questionnaire, Session


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
            'ttl_seconds',
            'created_at',
        )
        read_only_fields = (
            'id',
            'uuid',
            'created_at',
        )


class PublicSessionDetailedSerializer(PublicSessionSerializer):
    ...
