from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.signals.models import MainCategory, Signal, SubCategory
from signals.apps.signals.v1.serializers import (
    MainCategoryHALSerializer,
    PublicSignalCreateSerializer,
    PublicSignalSerializerDetail,
    SignalAttachmentSerializer,
    SubCategoryHALSerializer
)


class PublicSignalGenericViewSet(GenericViewSet):
    lookup_field = 'signal_id'
    lookup_url_kwarg = 'signal_id'

    is_public = True

    queryset = Signal.objects.all()

    pagination_class = None


class PublicSignalViewSet(CreateModelMixin, DetailSerializerMixin, RetrieveModelMixin,
                          PublicSignalGenericViewSet):

    serializer_class = PublicSignalCreateSerializer
    serializer_detail_class = PublicSignalSerializerDetail


class PublicSignalAttachmentsViewSet(CreateModelMixin, PublicSignalGenericViewSet):
    serializer_class = SignalAttachmentSerializer


class MainCategoryViewSet(DatapuntViewSet):
    queryset = MainCategory.objects.all()
    serializer_detail_class = MainCategoryHALSerializer
    serializer_class = MainCategoryHALSerializer
    lookup_field = 'slug'


class SubCategoryViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategoryHALSerializer
    pagination_class = HALPagination

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset,
                                main_category__slug=self.kwargs['slug'],
                                slug=self.kwargs['sub_slug'])
        self.check_object_permissions(self.request, obj)
        return obj
