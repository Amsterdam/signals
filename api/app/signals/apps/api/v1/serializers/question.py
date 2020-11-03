from datapunt_api.rest import HALSerializer
from rest_framework import serializers

from signals.apps.signals.models import Question


class PublicQuestionSerializerDetail(serializers.Serializer):
    key = serializers.CharField()
    field_type = serializers.ChoiceField(choices=Question.FIELD_TYPE_CHOICES)
    meta = serializers.JSONField()
    required = serializers.BooleanField()

    class Meta:
        fields = (
            'key',
            'field_type',
            'meta',
            'required',
        )


class PrivateQuestionSerializerDetail(HALSerializer):
    key = serializers.CharField()
    field_type = serializers.ChoiceField(choices=Question.FIELD_TYPE_CHOICES)
    meta = serializers.JSONField()
    required = serializers.BooleanField()

    class Meta:
        model = Question
        fields = (
            'id',
            'key',
            'field_type',
            'meta',
            'required',
        )
