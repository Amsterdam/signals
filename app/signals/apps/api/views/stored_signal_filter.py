# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from datapunt_api.pagination import HALPagination
from rest_framework import mixins, viewsets

from signals.apps.api.serializers import StoredSignalFilterSerializer
from signals.apps.signals.models import StoredSignalFilter
from signals.auth.backend import JWTAuthBackend


class StoredSignalFilterViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                                mixins.CreateModelMixin, mixins.UpdateModelMixin,
                                mixins.DestroyModelMixin, viewsets.GenericViewSet):
    authentication_classes = [JWTAuthBackend]

    pagination_class = HALPagination
    serializer_class = StoredSignalFilterSerializer

    def get_queryset(self):
        return StoredSignalFilter.objects.filter(created_by=self.request.user.username)
