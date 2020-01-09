from datapunt_api.rest import HALSerializer
from rest_framework import serializers

from signals.apps.signals.models import History, Signal


class HistoryHalSerializer(HALSerializer):
    _signal = serializers.PrimaryKeyRelatedField(queryset=Signal.objects.all())
    who = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()

    def get_who(self, obj):
        return obj.get_who()

    def get_description(self, obj):
        return obj.get_description()

    def get_action(self, obj):
        return obj.get_action()

    class Meta:
        model = History
        fields = (
            'identifier',
            'when',
            'what',
            'action',
            'description',
            'who',
            '_signal',
        )
