# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import HiddenField

from signals.apps.signals.models import Category, StatusMessage, StatusMessageCategory


class StatusMessageSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True, required=False)

    class Meta:
        model = StatusMessage
        fields = ['id', 'title', 'text', 'active', 'state', 'categories', 'updated_at', 'created_at']

    def _update_categories(self, instance: StatusMessage, categories_data: dict) -> StatusMessage:
        """
        Update the categories of the status message.
        """
        if categories_data is not None:
            current_categories = instance.categories.all()
            current_category_ids = set(category.id for category in current_categories)
            new_category_ids = set(category.id for category in categories_data)

            categories_to_add = Category.objects.filter(id__in=new_category_ids - current_category_ids)
            categories_to_remove = current_categories.filter(id__in=current_category_ids - new_category_ids)

            for category in categories_to_add:
                StatusMessageCategory.objects.create(status_message=instance, category=category, position=0)

            for category in categories_to_remove:
                instance.categories.remove(category)

        return instance

    def create(self, validated_data: dict) -> StatusMessage:
        """
        Create a new StatusMessage instance and set all categories.
        """
        categories_data = validated_data.pop('categories', None)
        instance = super().create(validated_data)
        return self._update_categories(instance, categories_data)

    def update(self, instance: StatusMessage, validated_data: dict) -> StatusMessage:
        """
        Update a StatusMessage instance and set all categories.
        """
        categories_data = validated_data.pop('categories', None)
        instance = super().update(instance, validated_data)
        return self._update_categories(instance, categories_data)


class CurrentCategoryDefault:
    requires_context = True

    def __call__(self, serializer_field):
        category_id = serializer_field.context['view'].kwargs.get('category_id')
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            raise ValidationError(f"Category with id {category_id} does not exist.")
        return category


class _StatusMessageCategoryPositionListSerializer(serializers.ListSerializer):
    def validate(self, attrs):
        errors = {}

        # Check if there are no duplicate status messages in the request
        status_messages = [attr['status_message'] for attr in attrs]
        if len(status_messages) != len(set(status_messages)):
            errors.update({'status_message': 'Duplicate status messages in request.'})

        # Check if there are no duplicate positions in the request
        positions = [attr['position'] for attr in attrs]
        if len(positions) != len(set(positions)):
            errors.update({'position': 'Duplicate positions in request.'})

        if errors:
            raise serializers.ValidationError(errors)

        return super().validate(attrs)


class StatusMessageCategoryPositionSerializer(serializers.Serializer):
    """
    Serializer for the StatusMessageCategory model used for ordering status messages.
    """
    status_message = serializers.IntegerField(min_value=1)
    category = HiddenField(default=CurrentCategoryDefault())
    position = serializers.IntegerField(min_value=0)

    class Meta:
        fields = ['status_message', 'category', 'position']
        list_serializer_class = _StatusMessageCategoryPositionListSerializer

    def validate(self, attrs):
        status_message_id = attrs['status_message']
        try:
            StatusMessage.objects.get(id=status_message_id)
        except StatusMessage.DoesNotExist:
            raise ValidationError({'status_message': f"Status message with id {status_message_id} does not exist."})

        return super().validate(attrs)

    def create(self, validated_data):
        status_message_id = validated_data['status_message']
        category = validated_data['category']
        position = validated_data['position']

        instance, _ = StatusMessageCategory.objects.update_or_create(status_message_id=status_message_id,
                                                                     category=category,
                                                                     defaults={'position': position})
        return validated_data
