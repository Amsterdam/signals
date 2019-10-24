from rest_framework import serializers

from signals.apps.users.models import Profile


class ProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            'created_at',
            'updated_at',
        )


class ProfileDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            'created_at',
            'updated_at',
        )
