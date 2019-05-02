from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.api.v1.serializers import (
    CategoryHALSerializer,
    ParentCategoryHALSerializer,
    PublicSignalAttachmentSerializer,
    PublicSignalCreateSerializer,
    PublicSignalSerializerDetail,
    StatusMessageTemplateSerializer
)
from signals.apps.signals.models import Category, Signal, Text


class PublicSignalGenericViewSet(GenericViewSet):
    lookup_field = 'signal_id'
    lookup_url_kwarg = 'signal_id'

    queryset = Signal.objects.all()

    pagination_class = None


class PublicSignalViewSet(CreateModelMixin, DetailSerializerMixin, RetrieveModelMixin,
                          PublicSignalGenericViewSet):
    serializer_class = PublicSignalCreateSerializer
    serializer_detail_class = PublicSignalSerializerDetail


class PublicSignalAttachmentsViewSet(CreateModelMixin, PublicSignalGenericViewSet):
    serializer_class = PublicSignalAttachmentSerializer


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

    def status_message_templates(self, *args, **kwargs):
        text_entries = Text.objects.filter(category=self.get_object())

        state_filter = self.request.query_params.get('state', None)
        if state_filter:
            text_entries = text_entries.filter(state=state_filter)

        serializer = StatusMessageTemplateSerializer(text_entries, many=True)
        return Response(serializer.data)


class NamespaceView(APIView):
    """
    Used for the curies namespace, at this moment it is just a dummy landing page so that we have
    a valid URI that resolves

    TODO: Implement HAL standard for curies in the future
    """

    def get(self, request):
        return Response()
