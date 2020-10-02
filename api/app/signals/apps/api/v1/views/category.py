from datapunt_api.rest import DatapuntViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from signals.apps.api.generics.mixins import UpdateModelMixin
from signals.apps.api.generics.permissions import ModelWritePermissions, SIAPermissions
from signals.apps.api.v1.serializers import (
    CategoryHALSerializer,
    ParentCategoryHALSerializer,
    PrivateCategorySerializer
)
from signals.apps.api.v1.serializers.category import PrivateCategoryHistoryHalSerializer
from signals.apps.signals.models import Category
from signals.auth.backend import JWTAuthBackend


class PublicCategoryViewSet(NestedViewSetMixin, DatapuntViewSet):
    queryset = Category.objects.all()
    lookup_field = 'slug'

    def get_queryset(self):
        if self.get_parents_query_dict():
            return super(PublicCategoryViewSet, self).get_queryset()
        return self.queryset.filter(parent__isnull=True)

    def get_serializer(self, *args, **kwargs):
        if self.get_parents_query_dict():
            serializer_class = CategoryHALSerializer
        else:
            serializer_class = ParentCategoryHALSerializer

        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)


class PrivateCategoryViewSet(UpdateModelMixin, DatapuntViewSet):
    serializer_class = PrivateCategorySerializer
    serializer_detail_class = PrivateCategorySerializer

    queryset = Category.objects.all()

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions & ModelWritePermissions,)

    @action(detail=True, url_path=r'history/?$')
    def history(self, request, pk=None):
        """
        The change log of the selected Category instance
        This is read-only!
        """
        category = self.get_object()
        serializer = PrivateCategoryHistoryHalSerializer(category.logs, many=True)
        return Response(serializer.data)
