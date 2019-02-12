"""
Views that are used exclusively by the V1 API
"""
from datapunt_api.pagination import HALPagination
from datapunt_api.rest import DatapuntViewSet
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic.detail import SingleObjectMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework_extensions.mixins import DetailSerializerMixin

from signals.apps.signals.api_generics.permissions import SIAPermissions
from signals.apps.signals.models import Attachment, History, MainCategory, Signal, SubCategory
from signals.apps.signals.pdf.views import PDFTemplateView
from signals.apps.signals.v1.filters import SignalFilter
from signals.apps.signals.v1.serializers import (
    HistoryHalSerializer,
    MainCategoryHALSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    PrivateSplitSignalSerializer,
    PublicSignalCreateSerializer,
    PublicSignalSerializerDetail,
    SignalAttachmentSerializer,
    SubCategoryHALSerializer
)
from signals.auth.backend import JWTAuthBackend


class MainCategoryViewSet(DatapuntViewSet):
    queryset = MainCategory.objects.all()
    serializer_detail_class = MainCategoryHALSerializer
    serializer_class = MainCategoryHALSerializer
    lookup_field = 'slug'


class SubCategoryViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
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


class PrivateSignalViewSet(DatapuntViewSet,
                           mixins.CreateModelMixin,
                           mixins.UpdateModelMixin):
    """Viewset for `Signal` objects in V1 private API"""
    queryset = Signal.objects.all()
    serializer_class = PrivateSignalSerializerList
    serializer_detail_class = PrivateSignalSerializerDetail
    pagination_class = HALPagination
    authentication_classes = (JWTAuthBackend,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = SignalFilter
    permission_classes = (SIAPermissions,)

    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'trace']

    @action(detail=True)
    def history(self, request, pk=None):
        """History endpoint filterable by action."""
        history_entries = History.objects.filter(_signal__id=pk)
        what = self.request.query_params.get('what', None)
        if what:
            history_entries = history_entries.filter(what=what)

        serializer = HistoryHalSerializer(history_entries, many=True)
        return Response(serializer.data)


class PrivateSignalSplitViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    serializer_class = PrivateSplitSignalSerializer
    queryset = Signal.objects.all()


class PublicSignalViewSet(mixins.CreateModelMixin,
                          DetailSerializerMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    queryset = Signal.objects.all()
    serializer_class = PublicSignalCreateSerializer
    serializer_detail_class = PublicSignalSerializerDetail
    lookup_field = 'signal_id'


class PublicSignalAttachmentsViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = SignalAttachmentSerializer
    signal = None
    is_public = True
    lookup_field = 'signal_id'
    lookup_url_kwarg = 'signal_id'

    def _get_signal(self):
        if self.signal is None:
            self.signal = Signal.objects.get(
                **{self.lookup_field: self.kwargs[self.lookup_url_kwarg]})

        return self.signal

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['signal'] = self._get_signal()
        context['is_public'] = self.is_public

        return context


class PrivateSignalAttachmentsViewSet(PublicSignalAttachmentsViewSet, mixins.ListModelMixin):
    is_public = False
    pagination_class = None
    lookup_field = 'pk'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return Attachment.actions.get_attachments(self._get_signal())


class GeneratePdfView(LoginRequiredMixin, SingleObjectMixin, PDFTemplateView):
    object = None
    pk_url_kwarg = 'signal_id'
    queryset = Signal.objects.all()

    template_name = 'signals/pdf/print_signal.html'
    extra_context = {'now': timezone.datetime.now(), }

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        self.pdf_filename = 'SIA-{}.pdf'.format(self.object.pk)
        rd_coordinates = self.object.location.get_rd_coordinates()
        bbox = '{},{},{},{}'.format(
            rd_coordinates.x - 340.00,
            rd_coordinates.y - 125.00,
            rd_coordinates.x + 340.00,
            rd_coordinates.y + 125.00,
        )
        return super(GeneratePdfView, self).get_context_data(bbox=bbox)
