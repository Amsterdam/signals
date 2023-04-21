# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from rest_framework import mixins, viewsets

from signals.apps.api.generics.permissions import ModelWritePermissions, SIAPermissions
from signals.apps.api.serializers.status_message import StatusMessageSerializer
from signals.apps.signals.models import StatusMessage
from signals.auth.backend import JWTAuthBackend


class StatusMessagesViewSet(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    """
    Endpoint to manage status messages.

    A status message can be used as a template for a response to a reporter on a state
    transition of a signal.

    Status messages contain a state field that links it to the
    state that the signal will be transitioned to and can be attached to multiple
    categories. Within each category it has a position, that can be used to determine
    the order in which the status messages should be displayed to the user.
    """
    queryset = StatusMessage.objects.all()
    serializer_class = StatusMessageSerializer
    authentication_classes = (JWTAuthBackend, )
    permission_classes = (SIAPermissions & ModelWritePermissions, )
