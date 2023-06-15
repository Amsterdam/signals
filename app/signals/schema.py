# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from drf_spectacular.openapi import AutoSchema
from rest_framework import serializers


class ErrorSerializer(serializers.Serializer):
    """
    Base serializer for error responses.
    """
    def to_internal_value(self, data):
        """
        Convert external representation to internal value.
        """
        return data

    def to_representation(self, instance):
        """
        Convert internal value to external representation.
        """
        return instance

    def update(self, instance, validated_data):
        """
        Perform update on the instance.
        """
        pass

    def create(self, validated_data):
        """
        Create a new instance.
        """
        pass


class ValidationErrorSerializer(ErrorSerializer):
    """
    Serializer for validation error responses.
    """
    errors = serializers.DictField(child=serializers.ListSerializer(child=serializers.CharField()))
    non_field_errors = serializers.ListSerializer(child=serializers.CharField())


class GenericErrorSerializer(ErrorSerializer):
    """
    Serializer for generic error responses.
    """
    detail = serializers.CharField()


class UnauthenticatedErrorSerializer(GenericErrorSerializer):
    """
    Serializer for unauthenticated error responses.
    """
    pass


class ForbiddenErrorSerializer(GenericErrorSerializer):
    """
    Serializer for forbidden error responses.
    """
    pass


class NotFoundErrorSerializer(GenericErrorSerializer):
    """
    Serializer for not found error responses.
    """
    pass


class InternalServerErrorSerializer(GenericErrorSerializer):
    """
    Serializer for internal server error responses.
    """
    pass


class SIGAutoSchema(AutoSchema):
    """
    Custom AutoSchema for Swagger/OpenAPI documentation.
    """
    def _get_error_response_bodies(self):
        """
        Get error response bodies based on the API method and authentication status.
        """
        error_codes = ['500', ]
        if not self.method == 'GET':
            error_codes.append('400')

        auth = self.get_auth()
        if auth and not any(item == {} for item in auth):
            error_codes.append('401')
            error_codes.append('403')

        if not (self.method == 'GET' and self._is_list_view()):
            if len(list(filter(lambda _: _['in'] == 'path', self._get_parameters()))):
                error_codes.append('404')

        self.error_response_bodies = {
            '400': self._get_response_for_code(ValidationErrorSerializer, '400'),
            '401': self._get_response_for_code(UnauthenticatedErrorSerializer, '401'),
            '403': self._get_response_for_code(ForbiddenErrorSerializer, '403'),
            '404': self._get_response_for_code(NotFoundErrorSerializer, '404'),
            '500': self._get_response_for_code(InternalServerErrorSerializer, '500'),
        }
        return {
            code: self.error_response_bodies[code]
            for code in error_codes
        }

    def _get_response_bodies(self, direction='response'):
        """
        Get response bodies for the API method.
        """
        responses = super()._get_response_bodies(direction=direction)
        if len(list(filter(lambda _: _.startswith('4'), responses.keys()))):
            return responses

        responses.update(self._get_error_response_bodies())
        return responses
