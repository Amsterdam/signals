# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from elasticsearch_dsl.response import Response
from rest_framework import serializers


class HighlightSerializer(serializers.Serializer):
    title = serializers.ListField(child=serializers.CharField(), required=False)
    text = serializers.ListField(child=serializers.CharField(), required=False)


class MetaSerializer(serializers.Serializer):
    highlight = HighlightSerializer(required=False)


class StatusMessageSearchResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    text = serializers.CharField()
    active = serializers.BooleanField()
    state = serializers.CharField()
    meta = MetaSerializer()


class TermsFacetSerializer(serializers.Serializer):
    count = serializers.SerializerMethodField()
    active = serializers.SerializerMethodField()

    def get_count(self, obj: tuple) -> int:
        return obj[1]

    def get_active(self, obj: tuple) -> bool:
        return obj[2]


class StateTermsFacetSerializer(TermsFacetSerializer):
    term = serializers.SerializerMethodField()

    def get_term(self, obj: tuple) -> str:
        return obj[0]


class ActiveTermsFacetSerializer(TermsFacetSerializer):
    term = serializers.SerializerMethodField()

    def get_term(self, obj: tuple) -> bool:
        return obj[0]


class StatusMessageFacetSerializer(serializers.Serializer):
    state = serializers.ListSerializer(child=StateTermsFacetSerializer())
    active = serializers.ListSerializer(child=ActiveTermsFacetSerializer())


class StatusMessageListSerializer(serializers.Serializer):
    count = serializers.SerializerMethodField()
    results = serializers.ListSerializer(child=StatusMessageSearchResultSerializer(), source='hits')
    facets = StatusMessageFacetSerializer()

    def get_count(self, obj: Response) -> int:
        return obj.hits.total.value
