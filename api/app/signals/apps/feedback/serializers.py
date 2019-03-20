from rest_framework import serializers

from signals.apps.feedback.models import Feedback, StandardAnswer


class StandardAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardAnswer
        fields = ('is_satisfied', 'text')


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ('is_satisfied', 'allows_contact', 'text')
        extra_kwargs = {
            'is_satisfied': {'write_only': True},
            'allows_contact': {'write_only': True},
            'text': {'write_only': True},
        }