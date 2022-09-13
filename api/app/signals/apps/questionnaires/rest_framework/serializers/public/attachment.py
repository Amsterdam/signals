# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import uuid

from django.core.files.storage import default_storage
from PIL.Image import DecompressionBombError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.questionnaires.fieldtypes.attachment import Attachment
from signals.apps.questionnaires.models import Question
from signals.apps.services.domain.filescanner import FileRejectedError


class PublicAttachmentSerializer(serializers.Serializer):
    question_uuid = serializers.UUIDField()
    file = serializers.FileField(required=True)

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

        file = validated_data.pop('file')
        try:
            question.get_field_type().validate_file(file)
        except (FileRejectedError, DecompressionBombError) as e:
            raise ValidationError({'file': [str(e)]})

        # Store the file in the default storage
        session_uuid = session_service.session.uuid
        random_uuid = uuid.uuid4()
        extension = file.name.split('.')[-1]
        path = f'{session_uuid.hex[:2]}/{session_uuid.hex[2:4]}/{session_uuid}/{random_uuid.hex}.{extension}'
        file_path = default_storage.save(f'attachments/questionnaires/sessions/{path}', file.file)

        payload = {'original_filename': file.name, 'file_path': file_path}
        return session_service.create_answer(payload, question)
