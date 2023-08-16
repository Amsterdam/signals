# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from signals.apps.api.filters.status_messages import StatusMessagesFilterSet
from signals.apps.api.generics.permissions import ModelWritePermissions, SIAPermissions
from signals.apps.api.serializers.status_message import (
    StatusMessageCategoryPositionSerializer,
    StatusMessageSerializer
)
from signals.apps.signals.models import StatusMessage, StatusMessageCategory
from signals.auth.backend import JWTAuthBackend


class StatusMessagesViewSet(ModelViewSet):
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
    filter_backends = (DjangoFilterBackend, OrderingFilter, )
    filterset_class = StatusMessagesFilterSet
    ordering = ('-created_at', )
    ordering_fields = ('created_at',
                       'updated_at',
                       ('statusmessagecategory__position', 'position'),)

    @transaction.atomic()
    def perform_create(self, serializer):
        super().perform_create(serializer)

    @transaction.atomic()
    def perform_update(self, serializer):
        super().perform_update(serializer)

    @transaction.atomic()
    def perform_destroy(self, instance):
        super().perform_destroy(instance)


class StatusMessagesCategoryPositionViewSet(CreateModelMixin, GenericViewSet):
    queryset = StatusMessageCategory.objects.all()
    serializer_class = StatusMessageCategoryPositionSerializer

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions & ModelWritePermissions,)
    filter_backends = ()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data, (list, )))

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)
