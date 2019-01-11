from rest_framework import serializers
from zds_client.client import ClientError

from signals.apps.signals.models import Signal


class SignalZDSSerializer(serializers.ModelSerializer):
    """Read-only serializer for `Signal` object."""
    id = serializers.IntegerField(label='ID', read_only=True)
    zds_case = serializers.SerializerMethodField()
    zds_statusses = serializers.SerializerMethodField()
    zds_images = serializers.SerializerMethodField()

    def get_zds_case(self, obj):
        if hasattr(obj, 'case'):
            try:
                return obj.case.get_case()
            except ClientError:
                return {}
        return {}

    def get_zds_statusses(self, obj):
        if hasattr(obj, 'case'):
            try:
                return obj.case.get_statusses()
            except ClientError:
                return []
        return []

    def get_zds_images(self, obj):
        if hasattr(obj, 'case'):
            try:
                return obj.case.get_images()
            except ClientError:
                return []
        return []

    class Meta(object):
        model = Signal
        fields = (
            'id',
            'zds_case',
            'zds_statusses',
            'zds_images',
        )
        read_only_fields = (
            'id',
            'zds_case',
            'zds_statusses',
            'zds_images',
        )
