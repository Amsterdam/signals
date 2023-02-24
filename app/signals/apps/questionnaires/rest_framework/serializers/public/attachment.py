# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
import uuid

from django.core.files.storage import default_storage
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.questionnaires.fieldtypes.attachment import Attachment
from signals.apps.questionnaires.models import Question


class PublicAttachmentSerializer(serializers.Serializer):
    question_uuid = serializers.UUIDField()
    file = serializers.ListField(child=serializers.FileField(required=True), required=True)

    def to_internal_value(self, data):
        """
        Convert incoming `file` field to a list with all uploaded files.
        """
        out = super().to_internal_value(data)
        out['file'] = data.getlist('file')
        return out

    def validate_question_uuid(self, value):
        try:
            question = Question.objects.get(uuid=value)
        except Question.DoesNotExist:
            raise ValidationError('Question does not exist')

        return question

    def create(self, validated_data):
        session_service = self.context['session_service']

        # The question_uuid is transformed to a Question object in the validate_question_uuid method
        question = validated_data.pop('question_uuid')
        if not issubclass(question.field_type_class, Attachment):
            raise ValidationError({'question': ['This question is not an attachment question']})

        # Check the number of uploaded files
        files = validated_data.pop('file')
        if len(files) == 0:
            raise ValidationError({'file': 'No File uploaded.'})

        if not question.multiple_answers_allowed and len(files) > 1:
            msg = 'Multiple uploaded files not allowed because multiple_answers_allowed is False.'
            raise ValidationError({'file': msg})

        # Create files on disk after they are validated
        answer_payload = []
        for file in files:
            question.get_field_type().validate_file(file)

            # Store the file in the default storage
            session_uuid = session_service.session.uuid
            random_uuid = uuid.uuid4()
            extension = file.name.split('.')[-1]
            path = f'{session_uuid.hex[:2]}/{session_uuid.hex[2:4]}/{session_uuid}/{random_uuid.hex}.{extension}'
            file_path = default_storage.save(f'attachments/questionnaires/sessions/{path}', file.file)
            answer_payload.append({'original_filename': file.name, 'file_path': file_path})

        # Make sure the downstream JSONSchema checks succeed if only one
        # upload is allowed.
        if not question.multiple_answers_allowed:
            answer_payload = answer_payload[0]

        return session_service.create_answer(answer_payload, question)
