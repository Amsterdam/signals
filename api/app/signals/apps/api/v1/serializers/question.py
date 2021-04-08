# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from rest_framework import serializers

from signals.apps.signals.models import Question


class PublicQuestionSerializerDetail(serializers.Serializer):
    key = serializers.CharField()
    field_type = serializers.ChoiceField(choices=Question.FIELD_TYPE_CHOICES)
    meta = serializers.JSONField()
    required = serializers.BooleanField()

    class Meta:
        fields = (
            'id',
            'key',
            'field_type',
            'meta',
            'required',
        )
