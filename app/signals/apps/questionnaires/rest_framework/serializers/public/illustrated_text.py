# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from rest_framework.serializers import ModelSerializer

from signals.apps.questionnaires.models.illustrated_text import IllustratedText
from signals.apps.questionnaires.rest_framework.serializers.public.attached_section import (
    NestedPublicAttachedSectionSerializer
)


class NestedPublicIllustratedTextSerializer(ModelSerializer):
    sections = NestedPublicAttachedSectionSerializer(many=True)

    class Meta:
        model = IllustratedText
        fields = (
            'title',
            'sections',
        )
