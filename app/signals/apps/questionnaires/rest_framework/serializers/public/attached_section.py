# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from signals.apps.questionnaires.models.attached_section import AttachedSection
from signals.apps.questionnaires.rest_framework.serializers.public.attached_file import (
    NestedPublicAttachedFileSerializer
)


class NestedPublicAttachedSectionSerializer(ModelSerializer):
    files = SerializerMethodField()

    class Meta:
        model = AttachedSection
        fields = (
            'header',
            'text',
            'files',
        )

    def get_files(self, obj):
        qs = obj.files.all().order_by('stored_file__id')
        return NestedPublicAttachedFileSerializer(qs, many=True, context=self.context).data
