# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import os

from datapunt_api.rest import DisplayField, HALSerializer
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.api.fields import (
    PrivateSignalAttachmentLinksField,
    PublicSignalAttachmentLinksField
)
from signals.apps.signals.models import Attachment, Signal


class SignalAttachmentSerializer(HALSerializer):
    _display = DisplayField()
    location = serializers.FileField(source='file', required=False)

    class Meta:
        model = Attachment
        fields = (
            '_display',
            '_links',
            'location',
            'is_image',
            'created_at',
            'file',
        )

        read_only = (
            '_display',
            '_links',
            'location',
            'is_image',
            'created_at',
        )

        extra_kwargs = {'file': {'write_only': True}}

    def create(self, validated_data):
        attachment = Signal.actions.add_attachment(validated_data['file'], self.context['view'].get_signal())

        if self.context['request'].user:
            attachment.created_by = self.context['request'].user.email
            attachment.save()

        return attachment

    def validate_file(self, file):
        if file.size > settings.API_MAX_UPLOAD_SIZE:
            msg = f'Bestand mag maximaal {settings.API_MAX_UPLOAD_SIZE} bytes groot zijn.'
            raise ValidationError(msg)

        _, ext = os.path.splitext(file.name)
        if ext.lower() not in ['.gif', '.jpg', '.jpeg', '.png']:
            msg = 'Bestandsextensie is niet toegestaan. Geldige extensies zijn: .gif, .jpg, .jpeg en .png.'
            raise ValidationError(msg)

        return file


class PublicSignalAttachmentSerializer(SignalAttachmentSerializer):
    serializer_url_field = PublicSignalAttachmentLinksField


class PrivateSignalAttachmentSerializer(SignalAttachmentSerializer):
    serializer_url_field = PrivateSignalAttachmentLinksField
