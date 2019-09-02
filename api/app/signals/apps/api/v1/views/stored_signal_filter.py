from datapunt_api.pagination import HALPagination
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework import viewsets

from signals.apps.api import mixins
from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.api.v1.serializers import (
    CountStoredSignalFilterSerializer,
    StoredSignalFilterSerializer
)
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


class CountStoredSignalFilterViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                                     viewsets.GenericViewSet):
    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions,)

    pagination_class = None
    serializer_class = CountStoredSignalFilterSerializer

    def get_queryset(self):
        return StoredSignalFilter.objects.filter(created_by=self.request.user.username)

    @method_decorator(cache_page(60*5))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        return super(CountStoredSignalFilterViewSet, self).list(
            request=request, *args, **kwargs
        )

    @method_decorator(cache_page(60 * 5))
    @method_decorator(vary_on_headers('Authorization'))
    def retrieve(self, request, *args, **kwargs):
        return super(CountStoredSignalFilterViewSet, self).retrieve(
            request=request, *args, **kwargs
        )
