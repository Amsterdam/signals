from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.feedback.models import Feedback, StandardAnswer


class StandardAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardAnswer
        fields = ('is_satisfied', 'text')


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ('is_satisfied', 'allows_contact', 'text', 'text_extra')
        # The 'required': True for is_satisfied field is only validated for JSON
        # updloads, a form upload defaults to False if is_satisfied is left out.
        # See the Django Rest Framework docs:
        # https://www.django-rest-framework.org/api-guide/fields/#booleanfield
        extra_kwargs = {
            'is_satisfied': {'write_only': True, 'required': True},
            'allows_contact': {'write_only': True},
            'text': {'write_only': True},
            'text_extra': {'write_only': True},
        }

    def update(self, instance, validated_data):
        validated_data['submitted_at'] = timezone.now()

        return super().update(instance, validated_data)
