# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from signals.apps.api.filters import SignalPromotedToParentFilter
from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.serializers import SignalIdListSerializer
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend

logger = logging.getLogger(__name__)


class SignalPromotedToParentViewSet(GenericViewSet, mixins.ListModelMixin):
    serializer_class = SignalIdListSerializer

    authentication_classes = [JWTAuthBackend]
    permission_classes = (SIAPermissions,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = SignalPromotedToParentFilter

    queryset = Signal.objects.prefetch_related('children').only('id').filter(children__isnull=False).order_by('-id')
