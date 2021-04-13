# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
"""
ViewSet that returns `signals.Signal` instance dropped out of a category.
"""
from datapunt_api.rest import HALPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from signals.apps.api.filters import SignalCategoryRemovedAfterFilterSet
from signals.apps.api.generics import mixins
from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.serializers import SignalIdListSerializer
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend


class SignalCategoryRemovedAfterViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SignalIdListSerializer
    pagination_class = HALPagination

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = SignalCategoryRemovedAfterFilterSet

    queryset = Signal.objects.only('id').all()
