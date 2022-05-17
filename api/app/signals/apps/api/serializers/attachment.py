# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import os
from datetime import timedelta

from datapunt_api.rest import DisplayField, HALSerializer
from django.conf import settings
from django.utils import timezone
from PIL.Image import DecompressionBombError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.api.fields import (
    PrivateSignalAttachmentLinksField,
    PublicSignalAttachmentLinksField
)
from signals.apps.feedback.app_settings import FEEDBACK_EXPECTED_WITHIN_N_DAYS
from signals.apps.feedback.models import Feedback
from signals.apps.services.domain.filescanner import FileRejectedError, UploadScannerService
from signals.apps.signals.models import Attachment, Signal
from signals.apps.signals.workflow import AFGEHANDELD, GEMELD, REACTIE_GEVRAAGD

PUBLIC_UPLOAD_ALLOWED_STATES = (AFGEHANDELD, GEMELD, REACTIE_GEVRAAGD)


class SignalAttachmentSerializerMixin:
    def create(self, validated_data):
        user = self.context['request'].user
        signal = self.context['view'].get_signal()

        # save our attachment
        attachment = Signal.actions.add_attachment(validated_data['file'], signal)
        if user:
            attachment.created_by = user.email
            attachment.save()

        # add a note that an attachment (currently only images allowed) was uploaded
        filename = os.path.basename(attachment.file.name)
        msg = f'Foto toegevoegd door melder: {filename}'
        if user:
            msg = f'Foto toegevoegd door {user.email}: {filename}'
        Signal.actions.create_note({'text': msg}, signal)

        return attachment

    def validate_file(self, file):
        if file.size > settings.API_MAX_UPLOAD_SIZE:
            msg = f'Bestand mag maximaal {settings.API_MAX_UPLOAD_SIZE} bytes groot zijn.'
            raise ValidationError(msg)

        try:
            UploadScannerService.scan_file(file)
        except (FileRejectedError, DecompressionBombError) as e:
            raise ValidationError(str(e))

        return file


class PublicSignalAttachmentSerializer(SignalAttachmentSerializerMixin, HALSerializer):
    serializer_url_field = PublicSignalAttachmentLinksField
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
        signal = self.context['view'].get_signal()
        if signal.status.state not in PUBLIC_UPLOAD_ALLOWED_STATES:
            msg = 'Public uploads not allowed in current signal state.'
            raise ValidationError(msg)

        # Only allow uploads in state AFGEHANDELD if there is an open/active
        # request for feedback from the reporter. Note several feedback requests
        # can be open/active at once.
        if signal.status.state == AFGEHANDELD:
            qs = (
                Feedback.objects.filter(_signal=signal)
                .filter(submitted_at__isnull=True)
                .filter(created_at__gte=timezone.now() - timedelta(days=FEEDBACK_EXPECTED_WITHIN_N_DAYS))
            )

            if not qs.exists():
                msg = 'No feedback expected for this signal hence no uploads allowed.'
                raise ValidationError(msg)

        return super().create(validated_data)


class PrivateSignalAttachmentSerializer(SignalAttachmentSerializerMixin, HALSerializer):
    serializer_url_field = PrivateSignalAttachmentLinksField

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
            'created_by',
        )

        read_only = (
            '_display',
            '_links',
            'location',
            'is_image',
            'created_at',
            'created_by',
        )

        extra_kwargs = {'file': {'write_only': True}}
