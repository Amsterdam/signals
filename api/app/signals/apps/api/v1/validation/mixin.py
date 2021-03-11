# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from django.conf import settings

from signals.apps.api.v1.validation.address.mixin import AddressValidationMixin


class SignalValidationMixin(AddressValidationMixin):
    @staticmethod
    def feature_enabled(feature_flag_name=None):
        return settings.FEATURE_FLAGS.get(feature_flag_name, True) if feature_flag_name else True

    def validate(self, attrs):
        if (self.feature_enabled('API_TRANSFORM_SOURCE_BASED_ON_REPORTER')
                and 'reporter' in attrs and 'email' in attrs['reporter']
                and attrs['reporter']['email']):
            reporter_email = attrs['reporter']['email']
            if (reporter_email not in settings.API_TRANSFORM_SOURCE_BASED_ON_REPORTER_EXCEPTIONS and
                    reporter_email.endswith(settings.API_TRANSFORM_SOURCE_BASED_ON_REPORTER_DOMAIN_EXTENSIONS)):
                attrs['source'] = settings.API_TRANSFORM_SOURCE_BASED_ON_REPORTER_SOURCE

        if (self.feature_enabled('API_TRANSFORM_SOURCE_IF_A_SIGNAL_IS_A_CHILD')
                and hasattr(settings, 'API_TRANSFORM_SOURCE_OF_CHILD_SIGNAL_TO')
                and 'parent' in attrs and attrs['parent']):
            attrs['source'] = settings.API_TRANSFORM_SOURCE_OF_CHILD_SIGNAL_TO

        return super().validate(attrs)
