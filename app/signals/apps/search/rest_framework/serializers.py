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


class TermFacetSerializer(serializers.Serializer):
    term = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()
    active = serializers.SerializerMethodField()

    def get_term(self, obj: tuple):
        return obj[0]

    def get_count(self, obj: tuple):
        return obj[1]

    def get_active(self, obj: tuple):
        return obj[2]


class StatusMessageFacetSerializer(serializers.Serializer):
    state = serializers.ListSerializer(child=TermFacetSerializer())
    active = serializers.ListSerializer(child=TermFacetSerializer())


class StatusMessageListSerializer(serializers.Serializer):
    # TODO: Rename hits to results
    hits = serializers.ListSerializer(child=StatusMessageSerializer())
    facets = StatusMessageFacetSerializer()
