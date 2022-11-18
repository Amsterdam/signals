# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from rest_framework.generics import RetrieveAPIView

from signals.apps.my_signals.models import Token
from signals.apps.my_signals.rest_framework.authentication import MySignalsTokenAuthentication
from signals.apps.my_signals.rest_framework.serializers.me import (
    MySignalsLoggedInReporterSerializer
)


class MySignalsLoggedInReporterView(RetrieveAPIView):
    """
    Detail for the currently logged in Reporter
    """
    queryset = Token.objects.none()

    authentication_classes = (MySignalsTokenAuthentication, )

    serializer_class = MySignalsLoggedInReporterSerializer
    pagination_class = None

    def get_object(self):
        return self.request.user
