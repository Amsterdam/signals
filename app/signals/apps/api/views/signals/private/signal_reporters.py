# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from signals.apps.api.filters.signal_reporter import ReporterFilterSet
from signals.apps.api.generics.permissions import ReporterPermission
from signals.apps.api.serializers.signal_reporter import SignalReporterSerializer
from signals.apps.signals.models import Reporter, Signal
from signals.auth.backend import JWTAuthBackend


class PrivateSignalReporterViewSet(CreateModelMixin, ListModelMixin, NestedViewSetMixin, GenericViewSet):
    queryset = Reporter.objects.all()
    filterset_class = ReporterFilterSet
    ordering_fields = ('-updated_at', )

    serializer_class = SignalReporterSerializer

    authentication_classes = (JWTAuthBackend, )
    permission_classes = (ReporterPermission, )

    def get_signal(self) -> Signal:
        """
        Used to return the signal instance for the current request. This is used
        to check the permissions for the current request.
        """
        return self.get_queryset().distinct().first()._signal
