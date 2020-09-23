from django.conf import settings
from rest_framework.serializers import ValidationError

from signals.apps.signals.models import Signal, Source


class SignalSourceValidator:
    requires_context = True

    def __call__(self, value, serializer_field):  # noqa: C901
        # Check if the given source is valid against the known sources in the database
        # For now this option is turned off for PROD/ACC in the FEATURE_FLAGS in the production.py settings file
        if settings.FEATURE_FLAGS.get('API_VALIDATE_SOURCE_AGAINST_SOURCE_MODEL', True):
            if not Source.objects.filter(name__iexact=value).exists():
                raise ValidationError('Invalid source given')

        # No need to check the given source this will be overwritten when creating the child Signal
        # For now this option is turned off for PROD/ACC in the FEATURE_FLAGS in the production.py settings file
        if (settings.FEATURE_FLAGS.get('API_TRANSFORM_SOURCE_IF_A_SIGNAL_IS_A_CHILD', True)
                and hasattr(settings, 'API_TRANSFORM_SOURCE_OF_CHILD_SIGNAL_TO')):
            if serializer_field.context['request'].data.get('parent', None):
                return value

        user = serializer_field.context['request'].user

        # If there is no user only the Signal.SOURCE_DEFAULT_ANONYMOUS_USER can be given as a source
        if not user and value.lower() != Signal.SOURCE_DEFAULT_ANONYMOUS_USER:
            raise ValidationError('Invalid source given for anonymous user')

        # If there is no user and the previous check did not raised an ValidationError we can use
        # the value. Otherwise we need to do some more checks
        if not user:
            return value

        # If the user is not authenticated only the Signal.SOURCE_DEFAULT_ANONYMOUS_USER can be
        # given as a source
        if not user.is_authenticated and value.lower() != Signal.SOURCE_DEFAULT_ANONYMOUS_USER:
            raise ValidationError('Invalid source given for anonymous user')

        # If the user is authenticated the Signal.SOURCE_DEFAULT_ANONYMOUS_USER CANNOT be given
        # as a source
        if user.is_authenticated and value.lower() == Signal.SOURCE_DEFAULT_ANONYMOUS_USER:
            raise ValidationError('Invalid source given for authenticated user')

        return value
