# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from typing import Optional

from django.utils import timezone
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from signals.apps.api.serializers.email_verification import EmailVerificationSerializer
from signals.apps.history.models import Log


class EmailVerificationView(APIView):
    serializer_class = EmailVerificationSerializer

    def post(self, request: Request, format: Optional[str] = None) -> Response:
        """Verify the token for reporter email verification."""
        data = JSONParser().parse(request.stream)
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        reporter = serializer.reporter
        reporter.email_verified = True
        reporter.approve()
        reporter.save()

        reporter.history_log.create(
            action=Log.ACTION_UPDATE,
            created_at=timezone.now(),
            description='E-mailadres is geverifieerd door de melder.',
            _signal=reporter._signal,
        )

        reporter.history_log.create(
            action=Log.ACTION_UPDATE,
            created_at=timezone.now(),
            description='E-mailadres is gewijzigd.',
            _signal=reporter._signal,
        )

        if reporter._signal.reporter.phone != reporter.phone:
            reporter.history_log.create(
                action=Log.ACTION_UPDATE,
                created_at=timezone.now(),
                description='Telefoonnummer is gewijzigd.',
                _signal=reporter._signal,
            )

        return Response(data=validated_data)
