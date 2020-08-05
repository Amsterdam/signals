"""
Views dealing with 'signals.Attachment' model directly.
"""
from datapunt_api.pagination import HALPagination
from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response

from signals.apps.api.generics import mixins
from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.v1.serializers import (
    PrivateSignalAttachmentSerializer,
    PublicSignalAttachmentSerializer
)
from signals.apps.api.v1.serializers.attachment import ImageOrUrlPostSerializer
from signals.apps.api.v1.views._base import PublicSignalGenericViewSet
from signals.apps.signals.models import Attachment, Signal
from signals.auth.backend import JWTAuthBackend


class PublicSignalAttachmentsViewSet(CreateModelMixin, PublicSignalGenericViewSet):
    serializer_class = PublicSignalAttachmentSerializer

    def create(self, request, signal_id):
        # Save POSTed file (whether directly or as URL)
        ls = ImageOrUrlPostSerializer(data=request.data, context=self.get_serializer_context())
        ls.is_valid(raise_exception=True)
        attachment = ls.save()

        # Return a serialization of the newly created attachment
        serializer = self.serializer_class(attachment, context=self.get_serializer_context())
        return Response(serializer.data, status=201)


class PrivateSignalAttachmentsViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                                      viewsets.GenericViewSet):
    serializer_class = PrivateSignalAttachmentSerializer
    pagination_class = HALPagination
    queryset = Attachment.objects.all()

    lookup_url_kwarg = 'pk'

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    def _filter_kwargs(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
        )

        return {self.lookup_field: self.kwargs[lookup_url_kwarg]}

    def get_object(self):
        self.lookup_field = self.lookup_url_kwarg

        obj = get_object_or_404(Signal.objects.all(), **self._filter_kwargs())
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        self.lookup_field = '_signal_id'

        qs = super(PrivateSignalAttachmentsViewSet, self).get_queryset()
        return qs.filter(**self._filter_kwargs())

    def create(self, request, pk):
        # Save POSTed file (whether directly or as URL)
        ls = ImageOrUrlPostSerializer(data=request.data, context=self.get_serializer_context())
        ls.is_valid(raise_exception=True)
        attachment = ls.save()

        # Return a serialization of the newly created attachment
        serializer = self.serializer_class(attachment, context=self.get_serializer_context())
        return Response(serializer.data, status=201)
