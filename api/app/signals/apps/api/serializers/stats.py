from rest_framework.fields import DateField, IntegerField
from rest_framework.serializers import Serializer


class TotalSerializer(Serializer):
    total = IntegerField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

class HighUrgencyCompletionSerializer(Serializer):
    date = DateField()
    amount = IntegerField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
