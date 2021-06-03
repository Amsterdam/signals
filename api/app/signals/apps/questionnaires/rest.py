# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DEFAULT_RENDERERS, _DisabledHTMLFilterBackend
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import mixins, viewsets
from rest_framework.relations import RelatedField
from rest_framework_extensions.mixins import DetailSerializerMixin


class HALViewSetRetrieve(DetailSerializerMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    renderer_classes = DEFAULT_RENDERERS
    pagination_class = HALPagination
    filter_backends = (_DisabledHTMLFilterBackend,)

    detailed_keyword = 'detailed'


class HALViewSetRetrieveCreateUpdate(DetailSerializerMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                                     mixins.UpdateModelMixin, viewsets.GenericViewSet):
    renderer_classes = DEFAULT_RENDERERS
    pagination_class = HALPagination
    filter_backends = (_DisabledHTMLFilterBackend,)

    detailed_keyword = 'detailed'


class UUIDRelatedField(RelatedField):
    default_error_messages = {
        'does_not_exist': 'Object does not exist.',
        'invalid': 'Invalid value given.',
    }

    def __init__(self, uuid_field=None, **kwargs):
        self.uuid_field = uuid_field or 'uuid'
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(**{self.uuid_field: data})
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.uuid_field, value=data)
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, obj):
        return getattr(obj, self.uuid_field)
