# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from datapunt_api.rest import DEFAULT_RENDERERS
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.views import APIView

from signals.apps.my_signals.mail import send_token_mail
from signals.apps.my_signals.models import Token
from signals.apps.my_signals.rest_framework.serializers.token import MySignalsTokenSerializer
from signals.apps.my_signals.rest_framework.throttling import AnonMySignalsTokenRateThrottle


class ObtainMySignalsTokenViewSet(APIView):
    """
    Based on the AuthToken implementation of rest-framework
    """
    throttle_classes = (AnonMySignalsTokenRateThrottle, )
    permission_classes = ()
    renderer_classes = DEFAULT_RENDERERS
    serializer_class = MySignalsTokenSerializer

    def get_serializer_context(self):
        return {'request': self.request, 'format': self.format_kwarg, 'view': self}

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Always return an HTTP 200 response with no body
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            reporter_email = serializer.validated_data['reporter_email']
            try:
                # Do we want to reuse any previous token if it is still valid? Or do we want to create a new token
                # and expire/remove old tokens?
                token = Token.objects.get(reporter_email=reporter_email, expires_at__gte=now())
            except Token.DoesNotExist:
                token = Token.objects.create(reporter_email=reporter_email)
            send_token_mail(token)

        return Response()
