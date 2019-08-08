from datapunt_api.rest import DisplayField, HALSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.api.v1.fields import (
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
        attachment = Signal.actions.add_attachment(validated_data['file'],
                                                   self.context['view'].get_object())

        if self.context['request'].user:
            attachment.created_by = self.context['request'].user.email
            attachment.save()

        return attachment

    def validate_file(self, file):
        if file.size > 8388608:  # 8MB = 8*1024*1024
            raise ValidationError("Bestand mag maximaal 8Mb groot zijn.")
        return file


class PublicSignalAttachmentSerializer(SignalAttachmentSerializer):
    serializer_url_field = PublicSignalAttachmentLinksField


class PrivateSignalAttachmentSerializer(SignalAttachmentSerializer):
    serializer_url_field = PrivateSignalAttachmentLinksField
