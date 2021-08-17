# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from datapunt_api.rest import DatapuntViewSet
from django_filters.rest_framework import DjangoFilterBackend

from signals.apps.api.serializers.source import SourceSerializer
from signals.apps.signals.models import Signal, Source
from signals.auth.backend import JWTAuthBackend


class PrivateSourcesViewSet(DatapuntViewSet):
    """
    Private ViewSet to display all sources, excluding the "online" (Signal.SOURCE_DEFAULT_ANONYMOUS_USER) source
    """
    serializer_class = SourceSerializer
    serializer_detail_class = SourceSerializer

    # Bug: SIG-3934
    #
    # The "online" source (Signal.SOURCE_DEFAULT_ANONYMOUS_USER) should not be returned in the response of
    # the private list endpoint. This source is only used when a anonymous user creates a Signal using the public
    # Signal endpoint
    queryset = Source.objects.exclude(name=Signal.SOURCE_DEFAULT_ANONYMOUS_USER)

    authentication_classes = (JWTAuthBackend, )

    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('is_active',)
