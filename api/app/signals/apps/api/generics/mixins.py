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
