# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DEFAULT_RENDERERS, _DisabledHTMLFilterBackend
from rest_framework import mixins, viewsets
from rest_framework_extensions.mixins import DetailSerializerMixin


class HALViewSetRetrieve(DetailSerializerMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    renderer_classes = DEFAULT_RENDERERS
    pagination_class = HALPagination
    filter_backends = (_DisabledHTMLFilterBackend,)

    detailed_keyword = 'detailed'


class HALViewSetRetrieveCreate(mixins.CreateModelMixin, HALViewSetRetrieve):
    def perform_create(self, serializer):
        return serializer.save()


class HALViewSetRetrieveCreateUpdate(mixins.UpdateModelMixin, HALViewSetRetrieveCreate):
    pass
