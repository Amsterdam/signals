# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from rest_framework import serializers

from signals.apps.signals.workflow import STATUS_CHOICES


class EmailPreviewSerializer(serializers.Serializer):
    subject = serializers.SerializerMethodField()
    html = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'subject',
            'html',
        )

    def get_subject(self, *args, **kwargs):
        email_preview = self.context.get('email_preview')
        return email_preview['subject'] if 'subject' in email_preview else ''

    def get_html(self, *args, **kwargs):
        email_preview = self.context.get('email_preview')
        return email_preview['html_message'] if 'html_message' in email_preview else ''


class EmailPreviewPostSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=STATUS_CHOICES, required=True)
    text = serializers.CharField(max_length=3000, required=False)
    email_override = serializers.EmailField(required=False, default=None)
