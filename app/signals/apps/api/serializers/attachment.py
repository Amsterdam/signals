# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import os
from datetime import timedelta

from datapunt_api.rest import DisplayField, HALSerializer
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.api.fields import (
    PrivateSignalAttachmentLinksField,
    PublicSignalAttachmentLinksField
)
from signals.apps.feedback.app_settings import FEEDBACK_EXPECTED_WITHIN_N_DAYS
from signals.apps.feedback.models import Feedback
from signals.apps.signals.models import Attachment, Signal
from signals.apps.signals.workflow import AFGEHANDELD, GEMELD, REACTIE_GEVRAAGD

PUBLIC_UPLOAD_ALLOWED_STATES = (AFGEHANDELD, GEMELD, REACTIE_GEVRAAGD)


class BaseSignalAttachmentSerializer(HALSerializer):
    _display = DisplayField()
    location = serializers.FileField(source='file', required=False, read_only=True)

    def create(self, validated_data: dict) -> Attachment:
        user = self.context['request'].user
        signal = self.context['view'].get_signal()

        # save our attachment
        attachment = Signal.actions.add_attachment(validated_data['file'], signal)
        if user.is_authenticated:
            attachment.created_by = user.email
            attachment.save()

        # add a note that an attachment (currently only images allowed) was uploaded
        filename = os.path.basename(attachment.file.name)
        if user.is_authenticated:
            Signal.actions.create_note({'text': f'Bijlage toegevoegd: {filename}', 'created_by': user}, signal)
        else:
            Signal.actions.create_note({'text': f'Bijlage toegevoegd door melder: {filename}'}, signal)

        return attachment


class PublicSignalAttachmentSerializer(BaseSignalAttachmentSerializer):
    serializer_url_field = PublicSignalAttachmentLinksField

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

        read_only_fields = (
            '_display',
            '_links',
            'location',
            'is_image',
            'created_at',
        )

        extra_kwargs = {'file': {'write_only': True}}

    def create(self, validated_data: dict) -> Attachment:
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

        attachment = super().create(validated_data)
        attachment.public = True
        attachment.save()

        return attachment


class PrivateSignalAttachmentSerializer(BaseSignalAttachmentSerializer):
    serializer_url_field = PrivateSignalAttachmentLinksField

    public = serializers.BooleanField(required=False)
    caption = serializers.CharField(required=False)

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
            'public',
            'caption',
        )

        read_only_fields = (
            '_display',
            '_links',
            'location',
            'is_image',
            'created_at',
            'created_by',
        )

        extra_kwargs = {'file': {'write_only': True}}


class PrivateSignalAttachmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ('public', 'caption')
