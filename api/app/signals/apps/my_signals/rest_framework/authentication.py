# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.utils.timezone import now
from rest_framework.authentication import TokenAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from signals.apps.my_signals.models import Token
from signals.apps.my_signals.rest_framework.utils import AuthenticatedReporter
from signals.apps.signals.models import Reporter


class MySignalsTokenAuthentication(TokenAuthentication):
    """
    Based on the AuthToken implementation of rest-framework
    """
    model = Token

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            raise AuthenticationFailed('No token provided.')

        return super().authenticate(request)

    def authenticate_credentials(self, key):
        model = self.get_model()

        try:
            token = model.objects.get(key=key, expires_at__gte=now())
        except model.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')

        if not Reporter.objects.filter(email__iexact=token.reporter_email).exists():
            raise AuthenticationFailed('Invalid token.')

        return AuthenticatedReporter(email=token.reporter_email), token
