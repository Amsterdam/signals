from rest_framework.serializers import IntegerField
from rest_framework.serializers import Serializer


class TotalSerializer(Serializer):
    total = IntegerField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
