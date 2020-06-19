from datapunt_api.pagination import HALPagination
from rest_framework import viewsets

from signals.apps.api.generics import mixins
from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.v1.serializers import StoredSignalFilterSerializer
from signals.apps.signals.models import StoredSignalFilter
from signals.auth.backend import JWTAuthBackend


class StoredSignalFilterViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                                mixins.CreateModelMixin, mixins.UpdateModelMixin,
                                mixins.DestroyModelMixin, viewsets.GenericViewSet):
    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    pagination_class = HALPagination
    serializer_class = StoredSignalFilterSerializer

    def get_queryset(self):
        return StoredSignalFilter.objects.filter(created_by=self.request.user.username)
