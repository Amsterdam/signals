# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from rest_framework.serializers import ModelSerializer

from signals.apps.questionnaires.models.attached_section import AttachedSection
from signals.apps.questionnaires.rest_framework.serializers.public.attached_file import (
    NestedPublicAttachedFileSerializer
)


class NestedPublicAttachedSectionSerializer(ModelSerializer):
    attached_files = NestedPublicAttachedFileSerializer(many=True)

    class Meta:
        model = AttachedSection
        fields = (
            'title',
            'text',

            'attached_files',
        )
