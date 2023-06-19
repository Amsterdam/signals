# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from django.contrib.auth.models import Group
from django.db.models.functions import Lower
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.viewsets import ModelViewSet
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.users.rest_framework.serializers import RoleSerializer
from signals.auth.backend import JWTAuthBackend


@extend_schema_view(
    list=extend_schema(description='List all roles'),
    retrieve=extend_schema(description='Retrieve a role'),
    partial_update=extend_schema(description='Update a role'),
    update=extend_schema(description='Update a role'),
    create=extend_schema(description='Create a role'),
    destroy=extend_schema(description='Delete a role'),
)
class RoleViewSet(DetailSerializerMixin, ModelViewSet):
    queryset = Group.objects.prefetch_related(
        'permissions',
        'permissions__content_type',
    ).order_by(Lower('name'))

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions & DjangoModelPermissions, )

    serializer_detail_class = RoleSerializer
    serializer_class = RoleSerializer
