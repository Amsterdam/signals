# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from collections import OrderedDict

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.email_integrations.services import MailService
from signals.apps.feedback.models import Feedback, StandardAnswer
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal


class StandardAnswerSerializer(serializers.ModelSerializer):
    topic = serializers.ReadOnlyField(source='topic.description', default=None)

    class Meta:
        model = StandardAnswer
        fields = ('is_satisfied', 'text', 'topic', 'open_answer', )


class FeedbackSerializer(serializers.ModelSerializer):
    signal_id = serializers.UUIDField(source='_signal.uuid', read_only=True)

    class Meta:
        model = Feedback
        fields = ('is_satisfied', 'allows_contact', 'text',
                  'text_list', 'text_extra', 'signal_id')
        # The 'required': True for is_satisfied field is only validated for JSON
        # updloads, a form upload defaults to False if is_satisfied is left out.
        # See the Django Rest Framework docs:
        # https://www.django-rest-framework.org/api-guide/fields/#booleanfield
        extra_kwargs = {
            'is_satisfied': {'write_only': True, 'required': True},
            'allows_contact': {'write_only': True},
            'text': {'write_only': True, 'required': False},
            'text_list': {'write_only': True, 'required': False},
            'text_extra': {'write_only': True},
        }

    def validate(self, attrs: dict) -> dict:
        # Attrs should have a text AND/OR a text_list if both are not present raise an error
        if not attrs.get('text') and not attrs.get('text_list'):
            raise ValidationError({'non_field_errors': ['Either text or text_list must be filled in']})

        # Set the submitted_at field to now
        attrs['submitted_at'] = timezone.now()

        # Merge the text and text_list to only text_list
        text = attrs.pop('text', None)
        text_list = attrs.get('text_list', [])
        if text:
            text_list.append(text)

        # Remove duplicate answers but keep the order intact
        ordered_text_dict = OrderedDict.fromkeys(text_list)
        attrs['text_list'] = list(ordered_text_dict.keys())

        # Call the super validate method
        return super().validate(attrs)

    def update(self, instance: Feedback, validated_data: dict) -> Feedback:
        instance = super().update(instance, validated_data)

        # Check if the Signal needs to be reopened
        if instance._signal.status and instance._signal.status.state != workflow.AFGEHANDELD:
            # The signal is not in the handled state, so no need to reopen
            return instance

        if validated_data['is_satisfied']:
            # The feedback is positive, so no need to reopen
            return instance

        q_filter = Q()
        for text in validated_data.get('text_list', []):
            q_filter.add(Q(text=text), Q.OR)

        sa_qs = StandardAnswer.objects.filter(q_filter)
        if sa_qs.count() < len(validated_data['text_list']) or sa_qs.filter(reopens_when_unhappy=True).exists():
            # A custom answer is given OR an answer that requires reopening is given
            payload = {'text': 'De melder is niet tevreden blijkt uit feedback. Zo nodig heropenen.',
                       'state': workflow.VERZOEK_TOT_HEROPENEN}
            Signal.actions.update_status(data=payload, signal=instance._signal)

        if instance._signal.allows_contact:
            # Send the mail to the reporter if the reporter allows contact
            MailService.system_mail(signal=instance._signal, action_name='feedback_received', feedback=instance)

        return instance
