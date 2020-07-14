from rest_framework import serializers

from signals.apps.signals.models import Source


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ('id', 'name', 'description', )
