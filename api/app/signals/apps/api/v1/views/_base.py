# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
"""
Viewset base classes, not to be used directly.
"""
from rest_framework.viewsets import GenericViewSet

from signals.apps.signals.models import Signal


class PublicSignalGenericViewSet(GenericViewSet):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Signal.objects.all()

    pagination_class = None
