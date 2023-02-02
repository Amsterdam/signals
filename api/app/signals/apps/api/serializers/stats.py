# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from rest_framework.fields import BooleanField, DateField, FloatField, IntegerField, ListField
from rest_framework.serializers import Serializer


class TotalSerializer(Serializer):
    total = IntegerField()
    results = ListField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CompletionSerializer(Serializer):
    date = DateField()
    amount = IntegerField()
    delta = FloatField()
    delta_increase = BooleanField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
