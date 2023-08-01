# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ReadOnlyModelViewSet

from signals.apps.api.filters.source import PrivateSourceFilterSet
from signals.apps.api.serializers.source import SourceSerializer
from signals.apps.signals.models import Source
from signals.auth.backend import JWTAuthBackend


class PrivateSourcesViewSet(ReadOnlyModelViewSet):
    """
    Display all sources
    """
    serializer_class = SourceSerializer

    queryset = Source.objects.all()

    authentication_classes = (JWTAuthBackend,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = PrivateSourceFilterSet
