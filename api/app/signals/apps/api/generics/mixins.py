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


class AddExtrasMixin:
    """Mixin class to add extra values to the validated data."""

    def add_user(self, data):
        request = self.context.get('request')
        if request.user and not request.user.is_anonymous:
            data['user'] = request.user.get_username()
        return data


class WriteOnceMixin:
    """
    Serializer mixin to make fields only writeable at creation. When updating the field is set to
    read-only.

    In the Meta data of the serializer just add tupple:

    write_once_fields = (
        '...',  # The name of the field you want to be write once
    )

    or list:

    write_once_fields = [
        '...',  # The name of the field you want to be write once
    ]
    """
    def get_extra_kwargs(self):
        extra_kwargs = super().get_extra_kwargs()
        action = getattr(self.context.get('view'), 'action', '')
        if action.lower() in ['update', 'partial_update']:
            extra_kwargs = self._set_write_once_fields(extra_kwargs)
        return extra_kwargs

    def _set_write_once_fields(self, extra_kwargs):
        write_once_fields = getattr(self.Meta, 'write_once_fields', None)
        if not write_once_fields:
            return extra_kwargs

        if not isinstance(write_once_fields, (list, tuple)):
            raise TypeError('The `write_once_fields` option must be a list or tuple. '
                            'Got {}.'.format(type(write_once_fields).__name__))

        for field_name in write_once_fields:
            kwargs = extra_kwargs.get(field_name, {})
            kwargs['read_only'] = True  # noqa This is where the magic happens and the field becomes write only
            extra_kwargs[field_name] = kwargs

        return extra_kwargs


class NearAmsterdamValidatorMixin:

    def validate_geometrie(self, value):
        fail_msg = 'Location coordinates not anywhere near Amsterdam. (in WGS84)'

        lat_not_in_adam_area = not 50 < value.coords[1] < 55
        lon_not_in_adam_area = not 1 < value.coords[0] < 7

        if lon_not_in_adam_area or lat_not_in_adam_area:
            raise DRFValidationError(fail_msg)
        return value
