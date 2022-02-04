# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2021 Gemeente Amsterdam
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


class PrivateSignalSourceValidator:
    requires_context = True

    def __call__(self, value, serializer_field):  # noqa: C901
        # Check if the given source is a valid active known source in the database
        if not Source.objects.filter(name__iexact=value, is_active=True).exists():
            raise ValidationError('Invalid source given, value not known')

        data = serializer_field.context['request'].data
        if isinstance(data, list):
            if data[0].get('parent', None):
                return value
        elif isinstance(data, dict):
            if data.get('parent', None):
                return value
        else:
            raise ValidationError('Signal source validation failed.')  # should never be hit

        # If the user is authenticated and the given Source is active and flagged as is_public raise a ValidationError
        if (serializer_field.context['request'].user.is_authenticated and
                Source.objects.filter(name__iexact=value, is_public=True, is_active=True).exists()):
            raise ValidationError('Invalid source given for authenticated user')

        return value
