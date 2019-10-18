from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins
from rest_framework.exceptions import ValidationError as DRFValidationError


def convert_validation_error(error):
    """
    Convert a Django ValidationError to a DRF ValidationError.
    """
    # TODO: handle Django ValidationError properties other than message
    if hasattr(error, 'message'):
        return DRFValidationError(error.message)
    else:
        return DRFValidationError('Validation error on underlying data.')


class CreateModelMixin(mixins.CreateModelMixin):
    def perform_create(self, serializer):
        try:
            return super(CreateModelMixin, self).perform_create(serializer=serializer)
        except DjangoValidationError as e:
            raise convert_validation_error(e)


class ListModelMixin(mixins.ListModelMixin):
    pass


class RetrieveModelMixin(mixins.RetrieveModelMixin):
    pass


class DestroyModelMixin(mixins.DestroyModelMixin):
    def perform_destroy(self, instance):
        try:
            instance.delete()
        except DjangoValidationError as e:
            raise convert_validation_error(e)


class UpdateModelMixin(mixins.UpdateModelMixin):
    def perform_update(self, serializer):
        try:
            return super(UpdateModelMixin, self).perform_update(serializer=serializer)
        except DjangoValidationError as e:
            raise convert_validation_error(e)


class FeatureFlagMixin:
    feature_flag_setting_kwarg = None

    def feature_enabled(self):
        return settings.FEATURE_FLAGS.get(self.feature_flag_setting_kwarg, False)
