# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.db import transaction
from django.utils import timezone
from django_fsm import TransitionNotAllowed
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from signals.apps.api.filters.signal_reporter import ReporterFilterSet
from signals.apps.api.generics.permissions import ReporterPermission
from signals.apps.api.serializers.signal_reporter import (
    CancelSignalReporterSerializer,
    SignalReporterSerializer
)
from signals.apps.history.models import Log
from signals.apps.signals.models import Reporter, Signal
from signals.auth.backend import JWTAuthBackend


class PrivateSignalReporterViewSet(CreateModelMixin, ListModelMixin, NestedViewSetMixin, GenericViewSet):
    queryset = Reporter.objects.all()
    filterset_class = ReporterFilterSet
    ordering_fields = ('-updated_at', )

    serializer_class = SignalReporterSerializer

    authentication_classes = [JWTAuthBackend]
    permission_classes = (ReporterPermission, )

    def get_signal(self) -> Signal:
        """
        Used to return the signal instance for the current request. This is used
        to check the permissions for the current request.
        """
        reporter = self.get_queryset().distinct().first()
        if not reporter:
            raise NotFound()

        return reporter._signal

    @extend_schema(request=CancelSignalReporterSerializer)
    @action(methods=['post'], detail=True, url_path='cancel', url_name='private-signal-reporter-cancel')
    def cancel(self, request: Request, *args, **kwargs):
        """
        Cancel a reporter, this allows cancelling a reporter update.
        Cancelling is allowed, when the state of the reporter is "new" or "verification_email_sent"
        and the reporter is not the original/first reporter of the signal.
        Optionally a reason for the cancellation can be provided using the reason field.
        """
        instance = self.get_object()
        cancel_serializer = CancelSignalReporterSerializer(data=request.data)
        cancel_serializer.is_valid(raise_exception=True)
        description = 'Contactgegevens wijziging geannuleerd'
        reason = cancel_serializer.validated_data.get('reason')
        if reason is None:
            description += '.'
        else:
            description += f': {reason}'

        try:
            self.perform_cancel(instance)

            instance.history_log.create(
                action=Log.ACTION_UPDATE,
                created_by=request.user,
                created_at=timezone.now(),
                description=description,
                _signal=instance._signal,
            )
        except TransitionNotAllowed:
            return Response(
                data={'non_field_errors': ['Cancelling this reporter is not possible.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @transaction.atomic()
    def perform_cancel(self, instance: Reporter) -> None:
        instance.cancel()
        instance.save()
