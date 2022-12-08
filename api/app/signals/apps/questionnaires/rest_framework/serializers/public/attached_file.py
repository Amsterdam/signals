# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from rest_framework.serializers import FileField, ModelSerializer

from signals.apps.questionnaires.models.attached_file import AttachedFile


class NestedPublicAttachedFileSerializer(ModelSerializer):
    file = FileField(source='stored_file.file')

    class Meta:
        model = AttachedFile
        fields = ('description', 'file')
