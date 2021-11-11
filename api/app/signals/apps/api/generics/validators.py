# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
from django.conf import settings
from rest_framework.serializers import ValidationError

from signals.apps.signals.models import Signal, Source


class PublicSignalSourceValidator:
    def __call__(self, value, *args, **kwargs):
        """
        On the public endpoint we only allow sources that are active and for public use only
        """
        if value.lower() == Signal.SOURCE_DEFAULT_ANONYMOUS_USER.lower():
            # No check is needed for the default source for anonymous users because it can or cannot be present in the
            # Database. This is how the API worked before we added this validator (SIG-4026)
            return value

        if not Source.objects.filter(name__iexact=value, is_public=True, is_active=True).exists():
            raise ValidationError('Invalid source given, value not known')
        return value


class SignalSourceValidator:
    requires_context = True

    def __call__(self, value, serializer_field):  # noqa: C901
        # Check if the given source is a valid active known source in the database
        if not Source.objects.filter(name__iexact=value, is_active=True).exists():
            raise ValidationError('Invalid source given, value not known')

        # No need to check the given source this will be overwritten when creating the child Signal
        # For now this option is turned off for PROD/ACC in the FEATURE_FLAGS in the production.py settings file
        if (settings.FEATURE_FLAGS.get('API_TRANSFORM_SOURCE_IF_A_SIGNAL_IS_A_CHILD', True)
                and hasattr(settings, 'API_TRANSFORM_SOURCE_OF_CHILD_SIGNAL_TO')):
            data = serializer_field.context['request'].data
            if isinstance(data, list):
                if data[0].get('parent', None):
                    return value
            elif isinstance(data, dict):
                if data.get('parent', None):
                    return value
            else:
                raise ValidationError('Signal source validation failed.')  # should never be hit

        user = serializer_field.context['request'].user

        if not user:
            # If there is no user check the following
            if value.lower() != Signal.SOURCE_DEFAULT_ANONYMOUS_USER:
                # The Signal.SOURCE_DEFAULT_ANONYMOUS_USER can be given as a source, if not raise an ValidationError
                # Default behaviour of the API
                raise ValidationError('Invalid source given for anonymous user')
            elif not Source.objects.filter(name__iexact=value, is_public=True, is_active=True).exists():
                # The given Source must be active and flagged as is_public otherwise raise an ValidationError
                raise ValidationError('Invalid source given for anonymous user')
            else:
                # If there is no user and the previous check did not raised an ValidationError we can use
                # the value. Otherwise we need to do some more checks
                return value

        # If the user is not authenticated only the Signal.SOURCE_DEFAULT_ANONYMOUS_USER can be
        # given as a source
        if not user.is_authenticated and value.lower() != Signal.SOURCE_DEFAULT_ANONYMOUS_USER:
            raise ValidationError('Invalid source given for anonymous user')

        # If the user is authenticated the Signal.SOURCE_DEFAULT_ANONYMOUS_USER CANNOT be given
        # as a source
        if user.is_authenticated and value.lower() == Signal.SOURCE_DEFAULT_ANONYMOUS_USER:
            raise ValidationError('Invalid source given for authenticated user')

        # If the user is not authenticated and the given Source is active and NOT flagged as is_public otherwise raise
        # an ValidationError
        if not user.is_authenticated and Source.objects.filter(name__iexact=value, is_public=False, is_active=True).exists():  # noqa
            raise ValidationError('Invalid source given for anonymous user')

        # If the user is authenticated and the given Source is active and flagged as is_public otherwise raise an
        # ValidationError
        if user.is_authenticated and Source.objects.filter(name__iexact=value, is_public=True, is_active=True).exists():
            raise ValidationError('Invalid source given for authenticated user')

        return value
