# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.utils import timezone
from rest_framework import serializers

from signals.apps.signals.models import Reporter


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

    reporter: Reporter

    def validate_token(self, token: str) -> str:
        try:
            self.reporter = Reporter.objects.get(email_verification_token=token)
        except Reporter.DoesNotExist:
            raise serializers.ValidationError("Token not found!")

        if self.reporter.email_verified:
            raise serializers.ValidationError("Token already verified!")

        if self.reporter.email_verification_token_expires < timezone.now():
            raise serializers.ValidationError("Token expired!")

        return token
