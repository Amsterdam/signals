# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
from datapunt_api.rest import DatapuntViewSet
from django.conf import settings
from django.contrib.auth.models import Permission
from django.db.models import Q
from rest_framework.permissions import DjangoModelPermissions

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.users.rest_framework.serializers import PermissionSerializer
from signals.auth.backend import JWTAuthBackend


class PermissionViewSet(DatapuntViewSet):
    queryset = Permission.objects.prefetch_related(
        'content_type',
    ).filter(Q(codename__istartswith='sia_') | Q(codename='push_to_sigmax'))

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions & DjangoModelPermissions,)

    serializer_detail_class = PermissionSerializer
    serializer_class = PermissionSerializer

    def get_queryset(self, *args, **kwargs):
        # TODO: Remove this when the frontend is updated
        qs = super(PermissionViewSet, self).get_queryset(*args, **kwargs)

        if exclude_permissions := settings.FEATURE_FLAGS.get('EXCLUDED_PERMISSIONS_IN_RESPONSE'):
            return qs.exclude(codename__in=exclude_permissions)
        else:
            return qs
