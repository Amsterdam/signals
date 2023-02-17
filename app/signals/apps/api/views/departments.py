# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from datapunt_api.rest import DatapuntViewSet, HALPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response

from signals.apps.api.filters import DepartmentFilterSet
from signals.apps.api.generics import mixins
from signals.apps.api.generics.permissions import ModelWritePermissions, SIAPermissions
from signals.apps.api.serializers import (
    PrivateDepartmentSerializerDetail,
    PrivateDepartmentSerializerList
)
from signals.apps.signals.models import Department
from signals.auth.backend import JWTAuthBackend


class PrivateDepartmentViewSet(mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               mixins.CreateModelMixin,
                               mixins.UpdateModelMixin,
                               DatapuntViewSet):
    queryset = Department.objects.all()

    serializer_class = PrivateDepartmentSerializerList
    serializer_detail_class = PrivateDepartmentSerializerDetail

    pagination_class = HALPagination

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions & ModelWritePermissions, )

    filter_backends = (DjangoFilterBackend, )
    filterset_class = DepartmentFilterSet

    ordering = ('-code', )

    def create(self, request, *args, **kwargs):
        # If we create a department we want to use the detail serializer
        serializer = self.serializer_detail_class(data=request.data,
                                                  context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
