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
from rest_framework.response import Response

from signals.apps.signals.api_generics.permissions import SIAPermissions
from signals.apps.signals.models import History, Signal
from signals.apps.signals.pdf.views import PDFTemplateView
from signals.apps.signals.v1.filters import SignalFilter
from signals.apps.signals.v1.serializers import (
    HistoryHalSerializer,
    PrivateSignalAttachmentSerializer,
    PrivateSignalSerializerDetail,
    PrivateSignalSerializerList,
    PrivateSplitSignalSerializer
)
from signals.auth.backend import JWTAuthBackend


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
    pagination_class = None


class PrivateSignalAttachmentsViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                                      viewsets.GenericViewSet):
    serializer_class = PrivateSignalAttachmentSerializer
    pagination_class = None

    queryset = Signal.objects.all()


class GeneratePdfView(LoginRequiredMixin, SingleObjectMixin, PDFTemplateView):
    object = None
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
