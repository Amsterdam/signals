# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Gemeente Amsterdam
import logging

from django.http import Http404
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from signals.apps.api.serializers import PublicSignalCreateSerializer, PublicSignalSerializerDetail
from signals.apps.signals.models import Signal
from signals.throttling import PostOnlyNoUserRateThrottle

logger = logging.getLogger(__name__)


class PublicSignalViewSet(GenericViewSet):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Signal.objects.all()

    pagination_class = None
    serializer_class = PublicSignalSerializerDetail

    throttle_classes = (PostOnlyNoUserRateThrottle,)

    def list(self, *args, **kwargs):
        raise Http404

    def create(self, request):
        serializer = PublicSignalCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        signal = serializer.save()

        data = PublicSignalSerializerDetail(signal, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, uuid):
        signal = get_object_or_404(Signal.objects.all(), uuid=uuid)
        data = PublicSignalSerializerDetail(signal, context=self.get_serializer_context()).data
        return Response(data)
