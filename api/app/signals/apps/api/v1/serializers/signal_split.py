"""
Serializer splits `api.Signal` instances in several children.
"""
import copy
from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoCoreValidationError
from django.db import OperationalError
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError

from signals.apps.api.generics.exceptions import PreconditionFailed
from signals.apps.api.v1.fields import PrivateSignalSplitLinksField
from signals.apps.api.v1.serializers.nested import _NestedSplitSignalSerializer
from signals.apps.signals import workflow
from signals.apps.signals.models import Category, Signal


class PrivateSplitSignalSerializer(serializers.Serializer):
    def validate(self, data):
        return self.to_internal_value(data)

    def to_internal_value(self, data):  # noqa: C901
        potential_parent_signal = self.context['view'].get_object()

        if potential_parent_signal.status.state == workflow.GESPLITST:
            raise PreconditionFailed('Signal has already been split')
        if potential_parent_signal.is_child():
            raise PreconditionFailed('A child signal cannot itself be split.')

        serializer = _NestedSplitSignalSerializer(data=data, many=True, context=self.context)
        serializer.is_valid()

        errors = OrderedDict()
        if not settings.SIGNAL_MIN_NUMBER_OF_CHILDREN <= len(
                self.initial_data) <= settings.SIGNAL_MAX_NUMBER_OF_CHILDREN:
            errors['children'] = 'A signal can only be split into min {} and max {} signals'.format(
                settings.SIGNAL_MIN_NUMBER_OF_CHILDREN, settings.SIGNAL_MAX_NUMBER_OF_CHILDREN
            )

        if errors:
            raise ValidationError(errors)

        output = {'children': copy.deepcopy(self.initial_data)}

        for item in output['children']:
            if 'type' in item and 'code' in item['type']:
                item['type'] = {'name': item['type']['code']}

            if 'category_url' in item['category'] and 'sub_category' in item['category']:
                del (item['category']['sub_category'])
            if 'category_url' in item['category']:
                item['category']['category_url'] = Category.objects.get_from_url(item['category']['category_url'])
            elif 'sub_category' in item['category']:
                item['category']['sub_category'] = Category.objects.get_from_url(item['category']['sub_category'])

        return output

    def to_representation(self, signal):
        if signal.children.count() == 0:
            raise NotFound('Split signal not found')

        links_field = PrivateSignalSplitLinksField(self.context['view'])
        nss = _NestedSplitSignalSerializer(signal.children.all(), many=True, context=self.context)

        return {
            '_links': links_field.to_representation(signal),
            'children': nss.data,
        }

    def create(self, validated_data):
        try:
            signal = Signal.actions.split(split_data=validated_data['children'],
                                          signal=self.context['view'].get_object(),
                                          user=self.context['request'].user)
        except (OperationalError, DjangoCoreValidationError):
            raise ValidationError('Could not perform split')

        return signal
