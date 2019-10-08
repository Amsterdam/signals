from django.utils import timezone
from rest_framework import serializers

from signals.apps.feedback.models import Feedback, StandardAnswer
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal


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
        # TODO: consider whether using a StandardAnswer while overriding the
        # is_satisfied field should be considered an error condition and return
        # an HTTP 400.
        validated_data['submitted_at'] = timezone.now()

        # Check whether the relevant Signal instance should possibly be
        # reopened (i.e. transition to VERZOEK_TOT_HEROPENEN state).
        is_satisfied = validated_data['is_satisfied']

        if is_satisfied:
            reopen = False
        else:
            feedback_text = validated_data['text']

            try:
                sa = StandardAnswer.objects.get(text=feedback_text)
            except StandardAnswer.DoesNotExist:
                reopen = True
            else:
                if not sa.is_satisfied:
                    reopen = sa.reopens_when_unhappy

        # Reopen the Signal (melding) if need be.
        if reopen:
            signal = instance._signal

            # Only allow a request to reopen when in state workflow.AFGEHANDELD
            if signal.status.state == workflow.AFGEHANDELD:
                payload = {
                    'text': 'De melder is niet tevreden blijkt uit feedback. Zo nodig heropenen.',
                    'state': workflow.VERZOEK_TOT_HEROPENEN,
                }
                Signal.actions.update_status(payload, signal)

        return super().update(instance, validated_data)
