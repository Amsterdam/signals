from django.core.exceptions import ImproperlyConfigured
from django_filters.rest_framework import filters
from rest_framework.filters import OrderingFilter

#
# Ordering
#


class FieldMappingOrderingFilter(OrderingFilter):
    """Extended version of the default DRF `OrderingFilter` class with support for field mappings.

    Usage:

        class MyViewSet(GenericViewSet):
            filter_backends = (FieldMappingOrderingFilter, ... )
            ordering_fields = (
                'created_at',
                'address'
                ...
            )
            ordering_field_mappings = {
                'created_at': 'created_at',
                'address': 'location__address_text',
                ...
            }
            ...
    """

    def get_field_mappings(self, view):
        """Get the field mappings dict.

        Used to map the given field name from the querystring (url) to the database field name on
        the database models.

        :param view: View object
        :raises: ImproperlyConfigured
        :returns: field mappings (dict)
        """
        # Validating if class is properly configurated.
        if not hasattr(view, 'ordering_field_mappings'):
            msg = (
                'Cannot use `{class_name}` on a view which does not have a '
                '`ordering_field_mappings` attribute configured.'
            )
            raise ImproperlyConfigured(msg.format(class_name=self.__class__.__name__))

        mapping_field_names = view.ordering_field_mappings.keys()
        if any(field not in mapping_field_names for field in view.ordering_fields):
            msg = (
                'Cannot use `{class_name}` on a view which does not have defined all fields in '
                '`ordering_fields` in the corresponding `ordering_field_mappings` attribute.'
            )
            raise ImproperlyConfigured(msg.format(class_name=self.__class__.__name__))

        return view.ordering_field_mappings

    def get_ordering(self, request, queryset, view):
        """Get a list with field names which is used for ordering the queryset.

        :param request: Request object
        :param queryset: Queryset object
        :param view: View object
        :returns: ordering fields (list) or None
        """
        ordering = super().get_ordering(request, queryset, view)
        if ordering:
            field_mappings = self.get_field_mappings(view)

            def find_field(field):
                mapped_field = field_mappings[field.lstrip('-')]
                if field.startswith('-'):
                    return f'-{mapped_field}'
                return mapped_field

            return list(map(find_field, ordering))

        return None


class OrderingExtraKwargsFilter(filters.OrderingFilter):
    def __init__(self, *args, **kwargs):
        self.extra_kwargs = kwargs.pop('extra_kwargs')
        super(OrderingExtraKwargsFilter, self).__init__(*args, **kwargs)

    def get_ordering_value(self, param):
        value = super(OrderingExtraKwargsFilter, self).get_ordering_value(param=param)

        descending = param.startswith('-')
        param = param[1:] if descending else param
        if param in self.extra_kwargs and self.extra_kwargs[param].get('apply', False):
            # Let's apply the given function that we want to use when ordering
            func = self.extra_kwargs[param]['apply']
            value = func(param).desc() if descending else func(param).asc()

        return value
