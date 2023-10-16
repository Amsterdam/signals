# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
from django.contrib.auth.models import Permission
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.users.rest_framework.serializers import PermissionSerializer
from signals.auth.backend import JWTAuthBackend


@extend_schema_view(
    list=extend_schema(description='List all permissions'),
    retrieve=extend_schema(description='Retrieve a permission'),
)
class PermissionViewSet(DetailSerializerMixin, ReadOnlyModelViewSet):
    queryset = Permission.objects.prefetch_related(
        'content_type',
    ).filter(Q(codename__istartswith='sia_') | Q(codename='push_to_sigmax'))

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions & DjangoModelPermissions,)

    serializer_detail_class = PermissionSerializer
    serializer_class = PermissionSerializer
