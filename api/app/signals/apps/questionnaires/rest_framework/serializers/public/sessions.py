# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers

from signals.apps.questionnaires.models import Session
from signals.apps.questionnaires.rest_framework.fields import SessionPublicHyperlinkedIdentityField
from signals.apps.questionnaires.rest_framework.serializers.public.illustrated_text import (
    NestedPublicIllustratedTextSerializer
)
from signals.apps.questionnaires.rest_framework.serializers.public.location import (
    LocationModelSerializer
)
from signals.apps.questionnaires.rest_framework.serializers.public.questions import (
    PublicQuestionSerializer
)


class PublicSessionSerializer(HALSerializer):
    serializer_url_field = SessionPublicHyperlinkedIdentityField

    _display = DisplayField()

    questionnaire_explanation = NestedPublicIllustratedTextSerializer(source='questionnaire.explanation')
    signal_snapshot = serializers.SerializerMethodField()
    can_freeze = serializers.SerializerMethodField()
    path_questions = serializers.SerializerMethodField()
    path_answered_question_uuids = serializers.SerializerMethodField()
    path_unanswered_question_uuids = serializers.SerializerMethodField()
    path_validation_errors_by_uuid = serializers.SerializerMethodField()

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
            'questionnaire_explanation',
            'signal_snapshot',
            # generated using the SessionService in serializer context:
            'can_freeze',
            'path_questions',
            'path_answered_question_uuids',
            'path_unanswered_question_uuids',
            'path_validation_errors_by_uuid'
        )
        read_only_fields = (
            'id',
            'uuid',
            'created_at',
            'questionnaire_explanation',
            'signal_snapshot',
            # generated using the SessionService in serializer context:
            'can_freeze',
            'path_questions',
            'path_path_answered_question_uuids',
            'path_unanswered_question_uuids',
            'path_validation_errors_by_uuid'
        )

    def get_can_freeze(self, obj):
        session_service = self.context.get('session_service')
        return session_service.can_freeze

    def get_path_questions(self, obj):
        session_service = self.context.get('session_service')
        serializer = PublicQuestionSerializer(session_service.path_questions, many=True, context=self.context)
        return serializer.data

    def get_path_answered_question_uuids(self, obj):
        session_service = self.context.get('session_service')
        return session_service.path_answered_question_uuids

    def get_path_unanswered_question_uuids(self, obj):
        session_service = self.context.get('session_service')
        return session_service.path_unanswered_question_uuids

    def get_path_validation_errors_by_uuid(self, obj):
        session_service = self.context.get('session_service')
        # Possibly turn all UUIDs into str(UUID)s in SessionService.
        return {str(k): v for k, v in session_service.path_validation_errors_by_uuid.items()}

    def get_signal_snapshot(self, obj):
        if not obj._signal:
            return None

        serialized_location = LocationModelSerializer(obj._signal_location).data
        serialized_location = serialized_location or None  # We want null in stead of {}
        return {
            'signal_id': obj._signal.uuid,
            'id': obj._signal.id,
            'location': serialized_location
        }

    def create(self, validated_data):
        """
        This serializer cannot be used to create Session instances
        """
        raise NotImplementedError

    def update(self, instance, validated_data):
        """
        This serializer cannot be used to update Session instances
        """
        raise NotImplementedError


class PublicSessionAnswerSerializer(serializers.Serializer):
    question_uuid = serializers.UUIDField()
    payload = serializers.JSONField()

    class Meta:
        fields = (
            'question_uuid',
            'payload',
        )
        read_only_fields = (
            'created_at',
        )
