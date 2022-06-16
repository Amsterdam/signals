# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2022 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
"""
Views dealing with 'signals.Attachment' model directly.
"""
import os

from datapunt_api.rest import DatapuntViewSet
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from signals.apps.api.generics import mixins
from signals.apps.api.serializers import (
    PrivateSignalAttachmentSerializer,
    PublicSignalAttachmentSerializer
)
from signals.apps.services.domain.permissions.signal import SignalPermissionService
from signals.apps.signals.models import Attachment, Signal
from signals.auth.backend import JWTAuthBackend


class PublicSignalAttachmentsViewSet(mixins.CreateModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Signal.objects.all()

    pagination_class = None
    serializer_class = PublicSignalAttachmentSerializer

    def get_signal(self):
        """
        The get_object will return a Signal instance. However, to keep the serializer working we needed to add a
        `get_signal` function which maps to the `get_object` function of the GenericViewSet class.
        """
        return self.get_object()


class PrivateSignalAttachmentsViewSet(
        NestedViewSetMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, DatapuntViewSet):
    queryset = Attachment.objects.all()

    serializer_class = PrivateSignalAttachmentSerializer
    serializer_detail_class = PrivateSignalAttachmentSerializer

    authentication_classes = (JWTAuthBackend,)

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        pk = self.kwargs.get('parent_lookup__signal__pk')
        signal_accessible = Signal.objects.filter(id=pk).filter_for_user(user).exists()

        if not SignalPermissionService.has_permission(user, 'signals.sia_can_view_all_categories'):
            if not signal_accessible:
                raise PermissionDenied()
        return super().get_queryset()

    def get_signal(self):
        pk = self.kwargs.get('parent_lookup__signal__pk')
        signal = get_object_or_404(Signal.objects.filter_for_user(self.request.user), pk=pk)
        return signal

    def destroy(self, *args, **kwargs):
        user = self.request.user
        signal = self.get_signal()
        attachment = self.get_object()

        if signal.is_parent and not user.has_perm('signals.sia_delete_attachment_of_parent_signal'):
            msg = 'Cannot delete attachment need "sia_delete_attachment_of_parent_signal" permission.'
            raise PermissionDenied(msg)
        elif signal.is_child and not user.has_perm('signals.sia_delete_attachment_of_child_signal'):
            msg = 'Cannot delete attachment need "sia_delete_attachment_of_child_signal" permission.'
            raise PermissionDenied(msg)
        elif (
                not signal.is_parent and
                not signal.is_child and
                not user.has_perm('signals.sia_delete_attachment_of_normal_signal')):
            msg = 'Cannot delete attachment need "sia_delete_attachment_of_normal_signal" permission.'
            raise PermissionDenied(msg)

        if attachment.created_by != user.email and not user.has_perm('signals.sia_delete_attachment_of_other_user'):
            msg = 'Cannot delete attachment need "sia_delete_attachment_of_other_user" permission.'
            raise PermissionDenied(msg)

        # We are not calling super().destroy(*args, **kwargs) here because that
        # would again run get_object() which we already did above.
        self.perform_destroy(attachment)

        att_filename = os.path.split(attachment.file.name)[1]
        Signal.actions.create_note({
            'text': f'Bijlage {att_filename} is verwijderd.', 'created_by': user
        }, signal=signal)
        return Response(status=status.HTTP_204_NO_CONTENT)
