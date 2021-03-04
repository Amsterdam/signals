# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from rest_framework import serializers

from signals.apps.signals.models import Attachment


class _NestedAttachmentModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = (
            'file',
            'created_at',
            'is_image',
        )
