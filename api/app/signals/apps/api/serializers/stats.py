# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
from rest_framework.fields import DateField, IntegerField
from rest_framework.serializers import Serializer


class TotalSerializer(Serializer):
    total = IntegerField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

class HighPriorityCompletionSerializer(Serializer):
    date = DateField()
    amount = IntegerField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
