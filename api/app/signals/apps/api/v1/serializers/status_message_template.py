import copy
from collections import OrderedDict

from rest_framework import serializers

from signals.apps.signals.models import StatusMessageTemplate
from signals.apps.signals.workflow import STATUS_CHOICES_API


class StateStatusMessageTemplateListSerializer(serializers.ListSerializer):
    def _get_states(self, representation):
        return list(OrderedDict.fromkeys([item['state'] for item in representation]))

    def _transform_state(self, state, representation):
        state_representation = OrderedDict(state=state, templates=[])
        for item in filter(lambda i: i['state'] == state, representation):
            state_representation['templates'].append(item['templates'])
        return state_representation

    def _transform_representation(self, representation):
        return [
            self._transform_state(state, representation)
            for state in self._get_states(representation)
        ]

    def to_representation(self, data):
        representation = super(StateStatusMessageTemplateListSerializer, self).to_representation(
            data=data
        )
        return self._transform_representation(representation)

    def to_internal_value(self, data):
        status_template_messages = []
        for item in data:
            status_template_message = {
                'state': item['state'],
                'category': self.context['category'],
            }

            if len(item['templates']):
                for order, template in enumerate(item['templates']):
                    status_template_message_copy = copy.copy(status_template_message)
                    status_template_message_copy.update({
                        'title': template['title'],
                        'text': template['text'],
                        'order': order,
                    })
                    status_template_messages.append(status_template_message_copy)
            else:
                status_template_messages.append(status_template_message)
        return status_template_messages

    def save(self, **kwargs):
        # Delete all status templates for each state we are adding, because we do a overwrite of
        # the complete set
        valid_states = [valid_data['state'] for valid_data in self.validated_data]
        StatusMessageTemplate.objects.filter(state__in=valid_states,
                                             category=self.context['category']).delete()

        # Actual creation of the status message templates
        for valid_data in self.validated_data:
            # If there is no title and no text we cannot add the template
            if 'title' in valid_data and 'text' in valid_data:
                StatusMessageTemplate.objects.create(**valid_data)


class StateStatusMessageTemplateSerializer(serializers.Serializer):
    state = serializers.ChoiceField(choices=STATUS_CHOICES_API, required=True)
    templates = serializers.SerializerMethodField(method_name='get_template')

    class Meta:
        list_serializer_class = StateStatusMessageTemplateListSerializer

    def get_template(self, obj):
        # See StateStatusMessageTemplateListSerializer to know how the templates are rendered in
        # lists. This serializer is always called with `many=True`
        return {
            'title': obj.title,
            'text': obj.text,
        }

    def validate(self, attrs):
        attrs.update({'category': self.context['category'].pk})
        return super(StateStatusMessageTemplateSerializer, self).validate(attrs)
