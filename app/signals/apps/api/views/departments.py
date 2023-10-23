# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.api.filters import DepartmentFilterSet
from signals.apps.api.generics.permissions import ModelWritePermissions, SIAPermissions
from signals.apps.api.serializers import (
    PrivateDepartmentSerializerDetail,
    PrivateDepartmentSerializerList
)
from signals.apps.signals.models import Department
from signals.auth.backend import JWTAuthBackend


@extend_schema_view(
    retrieve=extend_schema(description='Retrieve a department',
                           responses={HTTP_200_OK: PrivateDepartmentSerializerDetail}),
    update=extend_schema(responses={HTTP_200_OK: PrivateDepartmentSerializerDetail},
                         description='Update a department'),
    partial_update=extend_schema(responses={HTTP_200_OK: PrivateDepartmentSerializerDetail},
                                 description='Partial update a department'),
)
class PrivateDepartmentViewSet(CreateModelMixin, DetailSerializerMixin, UpdateModelMixin, ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    filterset_class = DepartmentFilterSet
    ordering = ('-code',)

    serializer_class = PrivateDepartmentSerializerList
    serializer_detail_class = PrivateDepartmentSerializerDetail

    authentication_classes = [JWTAuthBackend]
    permission_classes = (SIAPermissions & ModelWritePermissions,)

    @extend_schema(responses={HTTP_201_CREATED: PrivateDepartmentSerializerDetail},
                   description='Create a department')
    def create(self, request, *args: list, **kwargs: dict):
        # If we create a department, we want to use the detail serializer
        serializer = self.serializer_detail_class(data=request.data,
                                                  context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)
