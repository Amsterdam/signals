# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.fields import EmailField
from rest_framework.serializers import ModelSerializer

from signals.apps.my_signals.models import Token
from signals.apps.signals.models import Signal


class MySignalsTokenSerializer(ModelSerializer):
    """
    Based on the AuthToken implementation of rest-framework
    """
    email = EmailField(source='reporter_email', write_only=True)

    class Meta:
        model = Token
        fields = (
            'email',
        )

    def validate_email(self, value):
        queryset = Signal.objects.filter(
            reporter__email__iexact=value,  # Check if there are signals with a reporter matching the email address
            created_at__gte=timezone.now() - relativedelta(years=1)  # Only signals from the last 12 months
        ).exclude(
            parent__isnull=False  # Exclude all child signals
        )
        if not queryset.exists():
            raise ValidationError('Unable to request a token', code='authorization')
        return value
