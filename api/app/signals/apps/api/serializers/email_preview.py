# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from rest_framework import serializers


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
