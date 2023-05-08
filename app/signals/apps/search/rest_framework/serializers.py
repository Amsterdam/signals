from rest_framework import serializers


class HighlightSerializer(serializers.Serializer):
    title = serializers.ListField(child=serializers.CharField())
    text = serializers.ListField(child=serializers.CharField())


class MetaSerializer(serializers.Serializer):
    highlight = HighlightSerializer(required=False)


class StatusMessageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    text = serializers.CharField()
    active = serializers.BooleanField()
    state = serializers.CharField()
    meta = MetaSerializer()
