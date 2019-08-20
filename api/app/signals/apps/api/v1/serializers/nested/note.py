from rest_framework import serializers

from signals.apps.signals.models import Note


class _NestedNoteModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = (
            'text',
            'created_by',
        )
        read_only_fields = (
            'created_by',
        )
