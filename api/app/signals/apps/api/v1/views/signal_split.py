"""
ViewSet that splits `api.Signal` instances in several children.
"""
from rest_framework import viewsets
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.api.generics import mixins
from signals.apps.api.generics.permissions import SignalViewObjectPermission, SplitPermission
from signals.apps.api.v1.serializers import PrivateSplitSignalSerializer
from signals.apps.signals.models import Signal
from signals.auth.backend import JWTAuthBackend


class PrivateSignalSplitViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                                DetailSerializerMixin, viewsets.GenericViewSet):
    serializer_class = PrivateSplitSignalSerializer
    serializer_detail_class = PrivateSplitSignalSerializer
    queryset = Signal.objects.all()
    pagination_class = None

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SplitPermission,)
    object_permission_classes = (SignalViewObjectPermission,)

    def get_queryset(self, *args, **kwargs):
        if self._is_request_to_detail_endpoint():
            return super(PrivateSignalSplitViewSet, self).get_queryset(*args, **kwargs)
        else:
            qs = super(PrivateSignalSplitViewSet, self).get_queryset()
            return qs.filter_for_user(user=self.request.user)

    def check_object_permissions(self, request, obj):
        for permission_class in self.object_permission_classes:
            permission = permission_class()
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )
