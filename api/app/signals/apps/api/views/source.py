# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from datapunt_api.rest import DatapuntViewSet
from django_filters.rest_framework import DjangoFilterBackend

from signals.apps.api.serializers.source import SourceSerializer
from signals.apps.signals.models import Source
from signals.auth.backend import JWTAuthBackend


class PrivateSourcesViewSet(DatapuntViewSet):
    """
    V1 Private ViewSet to display all sources in the database
    """
    serializer_class = SourceSerializer
    serializer_detail_class = SourceSerializer

    queryset = Source.objects.all()

    authentication_classes = (JWTAuthBackend, )

    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('is_active',)
