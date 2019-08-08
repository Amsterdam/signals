from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from signals.apps.api.v1.serializers import CategoryHALSerializer, ParentCategoryHALSerializer
from signals.apps.signals.models import Category


class ParentCategoryViewSet(DatapuntViewSet):
    queryset = Category.objects.filter(parent__isnull=True)
    serializer_detail_class = ParentCategoryHALSerializer
    serializer_class = ParentCategoryHALSerializer
    lookup_field = 'slug'


class ChildCategoryViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryHALSerializer
    pagination_class = HALPagination

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        if 'slug' in self.kwargs and 'sub_slug' in self.kwargs:
            obj = get_object_or_404(queryset,
                                    parent__slug=self.kwargs['slug'],
                                    slug=self.kwargs['sub_slug'])
        else:
            obj = get_object_or_404(queryset, slug=self.kwargs['slug'])

        self.check_object_permissions(self.request, obj)
        return obj
