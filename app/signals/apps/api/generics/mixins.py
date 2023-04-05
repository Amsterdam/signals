# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam
from django.conf import settings
from rest_framework.exceptions import ValidationError as DRFValidationError


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


class WithinBoundingBoxValidatorMixin:

    def validate_geometrie(self, value):
        fail_msg = 'The location coordinates (WS84) are not inside the bounding box we are accepting signals for.'

        lat_not_in_bounding_box = not settings.BOUNDING_BOX[1] <= value.coords[1] <= settings.BOUNDING_BOX[3]
        lon_not_in_bounding_box = not settings.BOUNDING_BOX[0] <= value.coords[0] <= settings.BOUNDING_BOX[2]

        if lat_not_in_bounding_box or lon_not_in_bounding_box:
            raise DRFValidationError(fail_msg)

        return value
