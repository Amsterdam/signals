# Changes
import io

import requests
from datapunt_api.rest import DisplayField, HALSerializer
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.api.app_settings import SIGNALS_API_MAX_UPLOAD_SIZE
from signals.apps.api.v1.fields import (
    PrivateSignalAttachmentLinksField,
    PublicSignalAttachmentLinksField
)
from signals.apps.signals.models import Attachment, Signal


class ImageOrUrlPostSerializer(serializers.Serializer):
    location = serializers.URLField(required=False)
    file = serializers.FileField(required=False)

    def _file_from_url(self, url):
        response = requests.get(url, stream=True)
        buffer = io.BytesIO(response.content)

        # Prepare
        buffer.seek(0, 2)
        size = buffer.tell()
        buffer.seek(0, 0)

        f = InMemoryUploadedFile(
            buffer,
            field_name=None,
            name='test123',
            content_type=response.headers.get('content-type', 'text/plain'),
            size=size,
            charset=None,
        )
        return f

    def validate(self, validated_data):
        # Note: we abuse this validation method to figure out whether the file
        # was posted or a URL. In the latter case we download the associated
        # file and pretend the file was uploaded.
        # TODO:
        # * make REST GET/POST data for "location" field symmetrical
        # * consider whether this approach is safe/advisable
        # * implement limits on file download (time and size)
        if 'location' in validated_data and 'file' in validated_data:
            raise ValidationError('Do not set location and file fields simultaneously.')
        elif 'location' not in validated_data and 'file' not in validated_data:
            raise ValidationError('Either set location field or upload file.')

        # Download file assoctiated with url, store it on "file" field
        if 'location' in validated_data:
            url = validated_data.pop('location')
            f = self._file_from_url(url)
            validated_data['file'] = f

        if validated_data['file'].size > SIGNALS_API_MAX_UPLOAD_SIZE:
            msg = f'Bestand mag maximaal {SIGNALS_API_MAX_UPLOAD_SIZE} bytes groot zijn.'
            raise ValidationError(msg)

        return validated_data

    def create(self, validated_data):
        attachment = Signal.actions.add_attachment(validated_data['file'],
                                                   self.context['view'].get_object())

        if self.context['request'].user:
            attachment.created_by = self.context['request'].user.email
            attachment.save()

        return attachment


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

    def validate_file(self, file):
        if file.size > SIGNALS_API_MAX_UPLOAD_SIZE:
            msg = f'Bestand mag maximaal {SIGNALS_API_MAX_UPLOAD_SIZE} bytes groot zijn.'
            raise ValidationError(msg)
        return file


class PublicSignalAttachmentSerializer(SignalAttachmentSerializer):
    serializer_url_field = PublicSignalAttachmentLinksField


class PrivateSignalAttachmentSerializer(SignalAttachmentSerializer):
    serializer_url_field = PrivateSignalAttachmentLinksField
